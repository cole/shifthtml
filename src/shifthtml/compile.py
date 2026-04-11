"""Compile a ShiftHTML tree into a CompiledTemplate for fast repeated rendering.

Walks the tree once at compile time and generates a Python function via exec().
Static HTML becomes string literals, Var slots become inline resolution code,
conditionals become if/else blocks, and loops become for loops.
"""

from __future__ import annotations

import builtins
import textwrap
from collections.abc import AsyncGenerator, Callable, Generator
from html import escape as _html_escape
from string.templatelib import Interpolation, Template
from typing import Any

from .element import (
    Comment,
    ConditionalNode,
    Element,
    Fragment,
    IterationNode,
    Var,
)
from .lazy import Lazy
from .rendering import _collect_result, _convert, _needs_escape, render_open_tag
from .tree import Node, _render_vars
from .types import NodeContent, Renderable, is_node_list, is_sync_content_fn


class CompiledTemplate:
    """A compiled HTML template backed by a generated Python function."""

    __slots__ = ("_render_fn", "_source")

    _render_fn: Callable[[dict[str, object], list[str]], None]
    _source: str

    def __init__(self, render_fn: Callable[[dict[str, object], list[str]], None], source: str, /):
        self._render_fn = render_fn
        self._source = source

    def render(self, *, args: dict[str, object] | None = None) -> str:
        resolved = args or {}
        _render_vars.set(resolved)
        parts: list[str] = []
        self._render_fn(resolved, parts)
        return "".join(parts)

    def stream(self, *, args: dict[str, object] | None = None) -> Generator[str]:
        yield self.render(args=args)

    async def astream(self, *, args: dict[str, object] | None = None) -> AsyncGenerator[str]:
        yield self.render(args=args)

    def __str__(self) -> str:
        return self.render()

    def __repr__(self) -> str:
        return f"CompiledTemplate(<{len(self._source)} chars source>)"


def compile(node: Node | Fragment) -> CompiledTemplate:
    """Compile a node or fragment into a CompiledTemplate."""
    if isinstance(node, Fragment):
        node = node.root
    render_fn, source = _compile_to_function(node)
    return CompiledTemplate(render_fn, source)


# -- Code generation --


def _compile_to_function(
    node: Node,
) -> tuple[Callable[[dict[str, object], list[str]], None], str]:
    """Walk node tree, emit Python source, exec() it. Returns (render_fn, source)."""
    gen = _CodeGen()
    gen.visit_node(node)
    return gen.build()


class _CodeGen:
    def __init__(self) -> None:
        self._lines: list[str] = []
        self._indent: int = 2  # inside _make_render > _render
        self._closures: dict[str, object] = {}
        self._pending: list[str] = []
        self._counter: int = 0

    def _next_name(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}{self._counter}"

    def _emit(self, line: str) -> None:
        """Emit a dynamic code line, flushing any buffered static strings first."""
        self._flush_pending()
        self._lines.append("    " * self._indent + line)

    def _emit_block(self, block: str) -> None:
        """Emit a multi-line code block at the current indent level."""
        self._flush_pending()
        self._lines.append(textwrap.indent(block, "    " * self._indent))

    def _add_static(self, text: str) -> None:
        """Buffer a static string for merging with adjacent statics."""
        if text:
            self._pending.append(text)

    def _flush_pending(self) -> None:
        """Emit a single _a() call for all buffered static strings."""
        if self._pending:
            merged = "".join(self._pending)
            self._lines.append("    " * self._indent + f"_a({merged!r})")
            self._pending.clear()

    def _capture(self, prefix: str, value: object) -> str:
        """Register a closure variable and return its generated name."""
        name = self._next_name(prefix)
        self._closures[name] = value
        return name

    def build(self) -> tuple[Callable[[dict[str, object], list[str]], None], str]:
        """Assemble source, exec() it, return (render_fn, source)."""
        self._flush_pending()

        closure_params = ", ".join(self._closures) if self._closures else ""
        header = [
            f"def _make_render({closure_params}):",
            "    def _render(_vars, _buf):",
            "        _a = _buf.append",
        ]
        if not self._lines:
            header.append("        pass")
        footer = ["    return _render"]

        source = "\n".join(header + self._lines + footer)

        namespace: dict[str, Any] = {
            "_html_escape": _html_escape,
            "_needs_escape": _needs_escape,
            "_convert": _convert,
            "_collect_result": _collect_result,
            "Renderable": Renderable,
        }
        code = builtins.compile(source, "<shifthtml-codegen>", "exec")
        exec(code, namespace)  # noqa: S102
        render_fn = namespace["_make_render"](**self._closures)
        return render_fn, source

    # -- Node visitors --

    def visit_node(self, node: Node) -> None:
        match node:
            case Comment():
                self._add_static(f"<!--{node._escape_content()}-->")
            case Element():
                self._visit_element(node)
            case Lazy() if node._is_async:
                raise TypeError(
                    "compile() cannot eagerly resolve async Lazy nodes. "
                    "Only Var slots remain dynamic in compiled templates."
                )
            case Lazy():
                self._visit_lazy(node)
            case ConditionalNode():
                self._visit_conditional(node)
            case IterationNode():
                self._visit_iteration(node)
            case _:
                self._visit_children(node.children)

    def _visit_element(self, el: Element) -> None:
        if el.doctype:
            self._add_static(el.doctype)
        self._add_static(render_open_tag(el.tag, el._render_attrs(), void=el.void))
        if not el.void:
            self._visit_children(el.children)
            self._add_static(f"</{el.tag}>")

    def _visit_lazy(self, node: Lazy) -> None:
        if isinstance(node.fn, Var):
            self._emit_var_interpolation(node.fn)
        else:
            self._add_static(node.render())

    def _visit_conditional(self, node: ConditionalNode) -> None:
        self._emit(f"if _vars[{node.var.name!r}]:")
        self._indent += 1
        before = len(self._lines)
        self._emit_content(node.if_true)
        self._flush_pending()
        if len(self._lines) == before:
            self._lines.append("    " * self._indent + "pass")
        self._indent -= 1
        if node.if_false is not None:
            self._emit("else:")
            self._indent += 1
            before = len(self._lines)
            self._emit_content(node.if_false)
            self._flush_pending()
            if len(self._lines) == before:
                self._lines.append("    " * self._indent + "pass")
            self._indent -= 1

    def _visit_iteration(self, node: IterationNode) -> None:
        fn_name = self._capture("_fn", node.body_fn)
        item = self._next_name("_i")
        self._emit_block(f"""\
for {item} in _vars[{node.var.name!r}]:
    {fn_name}({item})._collect(_buf)""")

    def _visit_children(self, children: list) -> None:
        for child in children:
            match child:
                case str():
                    self._add_static(_html_escape(child) if _needs_escape(child) else child)
                case Template():
                    self._visit_template(child)
                case Node():
                    self.visit_node(child)

    def _visit_template(self, tpl: Template) -> None:
        for item in tpl:
            match item:
                case str():
                    self._add_static(item)
                case Interpolation():
                    self._emit_interpolation(item)

    def _emit_var_interpolation(self, var: Var) -> None:
        """Emit code for a Var used as a child node (may return Node or str)."""
        var_name = self._capture("_var", var)
        v = self._next_name("_v")
        self._emit_block(f"""\
{v} = {var_name}()
if isinstance({v}, Renderable):
    {v}._collect(_buf)
else:
    if not isinstance({v}, str):
        {v} = str({v})
    _a(_html_escape({v}) if _needs_escape({v}) else {v})""")

    def _emit_interpolation(self, interp: Interpolation) -> None:
        """Emit code for a single Template interpolation."""
        val_name = self._capture("_val", interp.value)
        v = self._next_name("_v")
        call = f"{val_name}()" if callable(interp.value) else val_name

        # Build the else branch: coerce to string, optional format, then escape
        else_lines = []
        if interp.conversion is not None:
            else_lines.append(f"{v} = _convert({v}, {interp.conversion!r})")
        else:
            else_lines.append(f"if not isinstance({v}, str):")
            else_lines.append(f"    {v} = str({v})")
        if interp.format_spec:
            else_lines.append(f"{v} = format({v}, {interp.format_spec!r})")
        else_lines.append(f"_a(_html_escape({v}) if _needs_escape({v}) else {v})")
        else_body = "\n".join("    " + line for line in else_lines)

        self._emit_block(f"""\
{v} = {call}
if isinstance({v}, Renderable):
    {v}._collect(_buf)
else:
{else_body}""")

    def _emit_content(self, content: NodeContent) -> None:
        """Emit code for arbitrary NodeContent (used in conditional branches)."""
        match content:
            case None | False:
                pass
            case str():
                self._add_static(_html_escape(content) if _needs_escape(content) else content)
            case Template():
                self._visit_template(content)
            case Fragment(root=root):
                self.visit_node(root)
            case Node():
                self.visit_node(content)
            case _ if is_node_list(content):
                for item in content:
                    self._emit_content(item)
            case _ if is_sync_content_fn(content):
                fn_name = self._capture("_lazy", content)
                self._emit(f"_collect_result({fn_name}(), _buf)")
