"""Compile a ShiftHTML tree into a Template for fast repeated rendering.

Partially evaluates the tree: static HTML and eagerly-resolved Lazy nodes
become string ops, while Var slots, conditionals, and loops become IR ops
that are evaluated at render time.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable, Generator
from dataclasses import dataclass
from html import escape as _html_escape
from string.templatelib import Interpolation
from string.templatelib import Template as StdlibTemplate
from typing import Any

from .element import (
    Async,
    Comment,
    ConditionalNode,
    Element,
    Fragment,
    IterationNode,
    Lazy,
    Node,
    Var,
    arender_result,
    render_result,
)
from .rendering import _needs_escape, arender_string, render, render_open_tag, render_string
from .tree import TreeNode, _render_vars
from .types import NodeContent, is_node_list, is_sync_content_fn

# -- IR types --


@dataclass(slots=True)
class Branch:
    """Conditional branch: resolves var at render time, picks a branch."""

    var_name: str
    if_true: list[RenderOp]
    if_false: list[RenderOp]


@dataclass(slots=True)
class Loop:
    """Iteration: resolves var at render time, calls body_fn per item."""

    var_name: str
    body_fn: Callable[[Any], NodeContent]


@dataclass(slots=True)
class LazySlot:
    """Opaque callable evaluated at render time (escape hatch)."""

    fn: Callable[..., NodeContent]


type RenderOp = str | StdlibTemplate | Branch | Loop | LazySlot


# -- Template --


class Template:
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
        return f"Template({self._ops!r})"


# -- Op execution --


def _exec_ops(ops: list[RenderOp], out: list[str]) -> None:
    for op in ops:
        match op:
            case str() as html:
                out.append(html)
            case StdlibTemplate() as tpl:
                out.extend(render_string(tpl))
            case Branch(var_name, if_true, if_false):
                branch = if_true if Var(var_name)() else if_false
                _exec_ops(branch, out)
            case Loop(var_name, body_fn):
                for item in Var(var_name)():
                    out.extend(render_result(body_fn(item), None))
            case LazySlot(fn):
                out.extend(render_result(fn(), None))


def _stream_ops(ops: list[RenderOp]) -> Generator[str]:
    for op in ops:
        match op:
            case str() as html:
                yield html
            case StdlibTemplate() as tpl:
                yield from render_string(tpl)
            case Branch(var_name, if_true, if_false):
                branch = if_true if Var(var_name)() else if_false
                yield from _stream_ops(branch)
            case Loop(var_name, body_fn):
                for item in Var(var_name)():
                    yield from render_result(body_fn(item), None)
            case LazySlot(fn):
                yield from render_result(fn(), None)


async def _astream_ops(ops: list[RenderOp]) -> AsyncGenerator[str]:
    for op in ops:
        match op:
            case str() as html:
                yield html
            case StdlibTemplate() as tpl:
                async for chunk in arender_string(tpl):
                    yield chunk
            case Branch(var_name, if_true, if_false):
                branch = if_true if Var(var_name)() else if_false
                async for chunk in _astream_ops(branch):
                    yield chunk
            case Loop(var_name, body_fn):
                for item in Var(var_name)():
                    async for chunk in arender_result(body_fn(item), None):
                        yield chunk
            case LazySlot(fn):
                async for chunk in arender_result(fn(), None):
                    yield chunk


# -- Compiler --


def compile(tree: Node | Fragment) -> Template:
    """Compile a node tree into a Template with Var slots and control flow."""
    root = tree.root if isinstance(tree, Fragment) else tree
    ops: list[RenderOp] = []
    _compile_node(root, ops)
    return Template(_merge_ops(ops))


def _compile_node(node: TreeNode, ops: list[RenderOp]) -> None:
    if isinstance(node, ConditionalNode):
        if_true_ops: list[RenderOp] = []
        _compile_content(node.if_true, if_true_ops)
        if_false_ops: list[RenderOp] = []
        if node.if_false is not None:
            _compile_content(node.if_false, if_false_ops)
        ops.append(Branch(node.var.name, if_true_ops, if_false_ops))
    elif isinstance(node, IterationNode):
        ops.append(Loop(node.var.name, node.body_fn))
    elif isinstance(node, Element):
        if node.doctype:
            ops.append(node.doctype)
        attrs = node._render_attrs()
        ops.append(render_open_tag(node.tag, attrs, void=node.void))
        if not node.void:
            _compile_children(node.children, ops)
            ops.append(f"</{node.tag}>")
    elif isinstance(node, Comment):
        ops.append(f"<!--{node._escape_content()}-->")
    elif isinstance(node, Lazy):
        if isinstance(node.fn, Var):
            ops.append(StdlibTemplate("", Interpolation(node.fn, node.fn.name, None, ""), ""))
        else:
            ops.append(render(node))
    elif isinstance(node, Async):
        raise TypeError(
            "compile() cannot eagerly resolve Async nodes. Only Var slots remain dynamic in compiled templates."
        )
    elif isinstance(node, Node):
        _compile_children(node.children, ops)


def _compile_children(children: list, ops: list[RenderOp]) -> None:
    for child in children:
        if isinstance(child, str):
            if _needs_escape(child):
                ops.append(_html_escape(child))
            else:
                ops.append(child)
        elif isinstance(child, StdlibTemplate):
            ops.append(child)
        elif isinstance(child, TreeNode):
            _compile_node(child, ops)


def _compile_content(content: NodeContent, ops: list[RenderOp]) -> None:
    """Compile arbitrary NodeContent into RenderOps (for conditional branches)."""
    if content is None or content is False:
        return
    if isinstance(content, str):
        if _needs_escape(content):
            ops.append(_html_escape(content))
        else:
            ops.append(content)
    elif isinstance(content, StdlibTemplate):
        ops.append(content)
    elif isinstance(content, Fragment):
        _compile_node(content.root, ops)
    elif isinstance(content, TreeNode):
        _compile_node(content, ops)
    elif is_node_list(content):
        for item in content:
            _compile_content(item, ops)
    elif is_sync_content_fn(content):
        ops.append(LazySlot(content))


def _merge_ops(ops: list[RenderOp]) -> list[RenderOp]:
    """Merge adjacent string ops and recursively merge Branch sub-lists."""
    merged: list[RenderOp] = []
    for op in ops:
        if isinstance(op, Branch):
            op = Branch(op.var_name, _merge_ops(op.if_true), _merge_ops(op.if_false))
        if isinstance(op, str) and merged and isinstance(merged[-1], str):
            merged[-1] += op
        else:
            merged.append(op)
    return merged
