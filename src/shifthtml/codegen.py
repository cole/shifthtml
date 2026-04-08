"""Compile a ShiftHTML node tree into a Python render function via exec()."""

from __future__ import annotations

from collections.abc import Callable
from html import escape as _html_escape
from string.templatelib import Interpolation, Template
from typing import Any

from .element import (
    Async,
    Comment,
    ConditionalNode,
    ContentNode,
    Element,
    Fragment,
    IterationNode,
    Lazy,
    Var,
)
from .rendering import _collect_result, _convert, _needs_escape, render_open_tag
from .tree import Node
from .types import NodeContent, Renderable, is_node_list, is_sync_content_fn


def compile_to_function(
    node: ContentNode,
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
        code = compile(source, "<shifthtml-codegen>", "exec")
        exec(code, namespace)  # noqa: S102
        render_fn = namespace["_make_render"](**self._closures)
        return render_fn, source

    # -- Node visitors --

    def visit_node(self, node: ContentNode) -> None:
        if isinstance(node, Comment):
            self._add_static(f"<!--{node._escape_content()}-->")
        elif isinstance(node, Element):
            self._visit_element(node)
        elif isinstance(node, Lazy):
            self._visit_lazy(node)
        elif isinstance(node, Async):
            raise TypeError(
                "compile() cannot eagerly resolve Async nodes. Only Var slots remain dynamic in compiled templates."
            )
        elif isinstance(node, ConditionalNode):
            self._visit_conditional(node)
        elif isinstance(node, IterationNode):
            self._visit_iteration(node)
        else:
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
        self._emit(f"for {item} in _vars[{node.var.name!r}]:")
        self._indent += 1
        self._emit(f"{fn_name}({item})._collect(_buf)")
        self._indent -= 1

    def _visit_children(self, children: list) -> None:
        for child in children:
            if isinstance(child, str):
                self._add_static(_html_escape(child) if _needs_escape(child) else child)
            elif isinstance(child, Template):
                self._visit_template(child)
            elif isinstance(child, ContentNode):
                self.visit_node(child)
            elif isinstance(child, Node):
                self._add_static("".join(child._stream()))

    def _visit_template(self, tpl: Template) -> None:
        for item in tpl:
            if isinstance(item, str):
                self._add_static(item)
            elif isinstance(item, Interpolation):
                self._emit_interpolation(item)

    def _emit_var_interpolation(self, var: Var) -> None:
        """Emit code for a Var used as a child node (may return Node or str)."""
        var_name = self._capture("_var", var)
        v = self._next_name("_v")
        self._emit(f"{v} = {var_name}()")
        self._emit(f"if isinstance({v}, Renderable):")
        self._indent += 1
        self._emit(f"{v}._collect(_buf)")
        self._indent -= 1
        self._emit("else:")
        self._indent += 1
        self._emit(f"if not isinstance({v}, str):")
        self._indent += 1
        self._emit(f"{v} = str({v})")
        self._indent -= 1
        self._emit(f"_a(_html_escape({v}) if _needs_escape({v}) else {v})")
        self._indent -= 1

    def _emit_interpolation(self, interp: Interpolation) -> None:
        """Emit code for a single Template interpolation."""
        val_name = self._capture("_val", interp.value)
        v = self._next_name("_v")

        if callable(interp.value):
            self._emit(f"{v} = {val_name}()")
        else:
            self._emit(f"{v} = {val_name}")

        self._emit(f"if isinstance({v}, Renderable):")
        self._indent += 1
        self._emit(f"{v}._collect(_buf)")
        self._indent -= 1
        self._emit("else:")
        self._indent += 1

        if interp.conversion is not None:
            self._emit(f"{v} = _convert({v}, {interp.conversion!r})")
        else:
            self._emit(f"if not isinstance({v}, str):")
            self._indent += 1
            self._emit(f"{v} = str({v})")
            self._indent -= 1

        if interp.format_spec:
            self._emit(f"{v} = format({v}, {interp.format_spec!r})")

        self._emit(f"_a(_html_escape({v}) if _needs_escape({v}) else {v})")
        self._indent -= 1

    def _emit_content(self, content: NodeContent) -> None:
        """Emit code for arbitrary NodeContent (used in conditional branches)."""
        if content is None or content is False:
            return
        if isinstance(content, str):
            self._add_static(_html_escape(content) if _needs_escape(content) else content)
            return
        if isinstance(content, Template):
            self._visit_template(content)
            return
        if isinstance(content, Fragment):
            root = content.root
            if isinstance(root, ContentNode):
                self.visit_node(root)
            else:
                self._add_static("".join(root._stream()))
            return
        if isinstance(content, Node):
            if isinstance(content, ContentNode):
                self.visit_node(content)
            else:
                self._add_static("".join(content._stream()))
            return
        if is_node_list(content):
            for item in content:
                self._emit_content(item)
            return
        if is_sync_content_fn(content):
            fn_name = self._capture("_lazy", content)
            self._emit(f"_collect_result({fn_name}(), _buf)")
