"""Compile a ShiftHTML tree into a Template for fast repeated rendering.

Partially evaluates the tree: static HTML and eagerly-resolved Lazy nodes
become Template string parts, while Var slots become Interpolation values
resolved at render time.
"""

from __future__ import annotations

from html import escape as _html_escape
from string.templatelib import Interpolation, Template

from .element import Async, Comment, Element, Fragment, Lazy, Node, Var
from .rendering import _needs_escape, render, render_open_tag
from .tree import TreeNode


def compile(tree: Node | Fragment) -> Template:
    """Compile a node tree into a Template with Var slots."""
    root = tree.root if isinstance(tree, Fragment) else tree
    parts: list[str | Interpolation] = []
    _compile_node(root, parts)
    return Template(*_merge_adjacent_strings(parts))


def _compile_node(node: TreeNode, parts: list[str | Interpolation]) -> None:
    if isinstance(node, Element):
        if node.doctype:
            parts.append(node.doctype)
        attrs = node._render_attrs()
        parts.append(render_open_tag(node.tag, attrs, void=node.void))
        if not node.void:
            _compile_children(node.children, parts)
            parts.append(f"</{node.tag}>")
    elif isinstance(node, Comment):
        parts.append(f"<!--{node._escape_content()}-->")
    elif isinstance(node, Lazy):
        if isinstance(node.fn, Var):
            parts.append(Interpolation(node.fn, node.fn.name, None, ""))
        else:
            parts.append(render(node))
    elif isinstance(node, Async):
        raise TypeError(
            "compile() cannot eagerly resolve Async nodes. Only Var slots remain dynamic in compiled templates."
        )
    elif isinstance(node, Node):
        _compile_children(node.children, parts)


def _compile_children(children: list, parts: list[str | Interpolation]) -> None:
    for child in children:
        if isinstance(child, str):
            if _needs_escape(child):
                parts.append(_html_escape(child))
            else:
                parts.append(child)
        elif isinstance(child, Template):
            for item in child:
                if isinstance(item, str | Interpolation):
                    parts.append(item)
        elif isinstance(child, TreeNode):
            _compile_node(child, parts)


def _merge_adjacent_strings(parts: list[str | Interpolation]) -> list[str | Interpolation]:
    merged: list[str | Interpolation] = []
    for part in parts:
        if isinstance(part, str) and merged and isinstance(merged[-1], str):
            merged[-1] += part
        else:
            merged.append(part)
    return merged
