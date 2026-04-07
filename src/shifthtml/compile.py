"""Compile a ShiftHTML tree into a CompiledTemplate for fast repeated rendering.

Partially evaluates the tree: static HTML and eagerly-resolved Lazy nodes
become string ops, while Var slots, conditionals, and loops become intermediate
representation ops that are evaluated at render time.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from html import escape as _html_escape
from string.templatelib import Interpolation, Template

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
from .operations import (
    Branch,
    LazySlot,
    Loop,
    RenderOp,
    _astream_ops,
    _exec_ops,
    _merge_ops,
    _stream_ops,
)
from .rendering import _needs_escape, render_open_tag
from .tree import Node, _render_vars
from .types import NodeContent, is_node_list, is_sync_content_fn

# -- CompiledTemplate --


class CompiledTemplate:
    """A compiled HTML template with variable slots and control flow."""

    __slots__ = ("_ops",)

    _ops: list[RenderOp]

    def __init__(self, ops: list[RenderOp], /):
        self._ops = ops

    def render(self, *, args: dict[str, object] | None = None) -> str:
        _render_vars.set(args or {})
        parts: list[str] = []
        _exec_ops(self._ops, parts)
        return "".join(parts)

    def stream(self, *, args: dict[str, object] | None = None) -> Generator[str]:
        _render_vars.set(args or {})
        return _stream_ops(self._ops)

    async def astream(self, *, args: dict[str, object] | None = None) -> AsyncGenerator[str]:
        _render_vars.set(args or {})
        async for chunk in _astream_ops(self._ops):
            yield chunk

    def __str__(self) -> str:
        return self.render()

    def __repr__(self) -> str:
        return f"CompiledTemplate({self._ops!r})"


# -- Public API --


def compile(node: ContentNode | Fragment) -> CompiledTemplate:
    """Compile a node or fragment into a CompiledTemplate."""
    if isinstance(node, Fragment):
        root = node.root
        if not isinstance(root, ContentNode):
            raise TypeError("Cannot compile a Fragment whose root is not a ContentNode")
        node = root
    ops: list[RenderOp] = []
    _compile_node(node, ops)
    return CompiledTemplate(_merge_ops(ops))


# -- Visitor dispatch --


def _compile_node(node: ContentNode, ops: list[RenderOp]) -> None:
    """Dispatch compilation to the appropriate handler based on node type."""
    if isinstance(node, Comment):
        ops.append(f"<!--{node._escape_content()}-->")
    elif isinstance(node, Element):
        _compile_element(node, ops)
    elif isinstance(node, Lazy):
        _compile_lazy(node, ops)
    elif isinstance(node, Async):
        raise TypeError(
            "compile() cannot eagerly resolve Async nodes. Only Var slots remain dynamic in compiled templates."
        )
    elif isinstance(node, ConditionalNode):
        _compile_conditional(node, ops)
    elif isinstance(node, IterationNode):
        ops.append(Loop(node.var.name, node.body_fn))
    else:
        _compile_children(node.children, ops)


def _compile_element(el: Element, ops: list[RenderOp]) -> None:
    if el.doctype:
        ops.append(el.doctype)
    ops.append(render_open_tag(el.tag, el._render_attrs(), void=el.void))
    if not el.void:
        _compile_children(el.children, ops)
        ops.append(f"</{el.tag}>")


def _compile_lazy(node: Lazy, ops: list[RenderOp]) -> None:
    if isinstance(node.fn, Var):
        ops.append(Template("", Interpolation(node.fn, node.fn.name, None, ""), ""))
    else:
        ops.append(node.render())


def _compile_conditional(node: ConditionalNode, ops: list[RenderOp]) -> None:
    if_true_ops: list[RenderOp] = []
    _compile_content(node.if_true, if_true_ops)
    if_false_ops: list[RenderOp] = []
    if node.if_false is not None:
        _compile_content(node.if_false, if_false_ops)
    ops.append(Branch(node.var.name, if_true_ops, if_false_ops))


def _compile_children(children: list, ops: list[RenderOp]) -> None:
    for child in children:
        if isinstance(child, str):
            ops.append(_html_escape(child) if _needs_escape(child) else child)
        elif isinstance(child, Template):
            ops.append(child)
        elif isinstance(child, Node):
            if isinstance(child, ContentNode):
                _compile_node(child, ops)
            else:
                ops.append("".join(child._stream()))


def _compile_content(content: NodeContent, ops: list[RenderOp]) -> None:
    """Compile arbitrary NodeContent into RenderOps (for conditional branches)."""
    if content is None or content is False:
        return
    if isinstance(content, str):
        ops.append(_html_escape(content) if _needs_escape(content) else content)
    elif isinstance(content, Template):
        ops.append(content)
    elif isinstance(content, Fragment):
        root = content.root
        if isinstance(root, ContentNode):
            _compile_node(root, ops)
        else:
            ops.append("".join(root._stream()))
    elif isinstance(content, Node):
        if isinstance(content, ContentNode):
            _compile_node(content, ops)
        else:
            ops.append("".join(content._stream()))
    elif is_node_list(content):
        for item in content:
            _compile_content(item, ops)
    elif is_sync_content_fn(content):
        ops.append(LazySlot(content))
