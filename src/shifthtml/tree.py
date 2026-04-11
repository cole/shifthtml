"""
Abstract base class for nodes in a tree structure, analogous to DOM nodes.
"""

from __future__ import annotations

import copy
from collections.abc import AsyncGenerator, Generator, Iterator
from contextvars import ContextVar
from string.templatelib import Template
from typing import TYPE_CHECKING, Any, Literal, Self, overload

import anyio

from .rendering import (
    RenderContext,
    aflush_deferred,
    astream_children,
    flush_deferred,
    stream_children,
)
from .types import _MISSING

if TYPE_CHECKING:
    from .element import Fragment
    from .types import NodeContent

_render_vars: ContextVar[dict[str, object] | None] = ContextVar("shifthtml.render_vars", default=None)

type ChildNode = Node | str | Template

_EMPTY_ARGS: dict[str, object] = {}


def _resolve_var(name: str, default: object = _MISSING) -> Any:
    """Look up a render-time variable by name. Used by compiled template execution."""
    vars = _render_vars.get()
    if vars and name in vars:
        return vars[name]
    if default is not _MISSING:
        return default
    raise LookupError(f"Var {name!r} not set")


class Node:
    """
    Abstract base class for all nodes in the document tree.

    Analogous to the DOM Node interface. Manages parent/child relationships,
    provides tree traversal, and supports rendering to HTML via _chunks()/_achunks().

    The >> operator creates a Fragment for building HTML trees.
    """

    __slots__ = ("parent_node", "children")

    parent_node: None | Node
    children: list[ChildNode]

    def __init__(self):
        self.parent_node = None
        self.children = []

    def _collect(self, buf: list[str]) -> None:
        """Collect HTML chunks into a buffer. Default delegates to _chunks()."""
        buf.extend(self._chunks())

    def _chunks(self, ctx: RenderContext | None = None) -> Generator[str]:
        """Yield HTML chunks for this node. Default renders children."""
        yield from stream_children(self.children, ctx)

    async def _achunks(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        """Yield HTML chunks asynchronously. Default renders children."""
        async for chunk in astream_children(self.children, ctx):
            yield chunk

    def render(
        self,
        *,
        args: dict[str, object] | None = None,
        max_depth: int = 100,
        max_nodes: int | None = None,
    ) -> str:
        """Render this node to an HTML string."""
        _render_vars.set(args if args is not None else _EMPTY_ARGS)
        ctx = RenderContext(max_depth=max_depth, max_nodes=max_nodes, _root_node=self)
        parts = list(self._chunks(ctx))
        parts.extend(flush_deferred(ctx))
        return "".join(parts)

    def stream(
        self,
        *,
        args: dict[str, object] | None = None,
        max_depth: int = 100,
        max_nodes: int | None = None,
    ) -> Generator[str]:
        """Yield HTML chunks for this node."""
        _render_vars.set(args or {})
        ctx = RenderContext(max_depth=max_depth, max_nodes=max_nodes, _root_node=self)
        yield from self._chunks(ctx)
        yield from flush_deferred(ctx)

    async def astream(
        self,
        *,
        args: dict[str, object] | None = None,
        min_chunk_size: int | None = 4096,
        cancel_scope: anyio.CancelScope | None = None,
        max_depth: int = 100,
        max_nodes: int | None = None,
    ) -> AsyncGenerator[str]:
        """Yield HTML chunks asynchronously with optional batching."""
        _render_vars.set(args or {})
        if min_chunk_size is None:
            async for chunk in self._achunks_unbuffered(
                cancel_scope=cancel_scope, max_depth=max_depth, max_nodes=max_nodes
            ):
                yield chunk
            return

        buf: list[str] = []
        buf_size = 0
        async for chunk in self._achunks_unbuffered(
            cancel_scope=cancel_scope, max_depth=max_depth, max_nodes=max_nodes
        ):
            buf.append(chunk)
            buf_size += len(chunk)
            if buf_size >= min_chunk_size:
                yield "".join(buf)
                buf.clear()
                buf_size = 0
        if buf:
            yield "".join(buf)

    async def _achunks_unbuffered(
        self,
        *,
        cancel_scope: anyio.CancelScope | None = None,
        max_depth: int = 100,
        max_nodes: int | None = None,
    ) -> AsyncGenerator[str]:
        ctx = RenderContext(cancel_scope=cancel_scope, max_depth=max_depth, max_nodes=max_nodes, _root_node=self)
        async for chunk in self._achunks(ctx):
            yield chunk
        async for chunk in aflush_deferred(ctx):
            yield chunk

    @overload
    def __rshift__(self, other: NodeContent) -> Fragment: ...  # noqa: F821

    @overload
    def __rshift__(self, other: None) -> None: ...

    @overload
    def __rshift__(self, other: Literal[False]) -> None: ...

    def __rshift__(self, other):
        if other is None or other is False:
            return None
        # _Fragment is set by element.py at import time to avoid circular imports.
        assert _Fragment is not None
        return _Fragment(self, self).__rshift__(other)

    @property
    def text_content(self) -> str:
        """Get the text content of this node and all descendants."""
        parts: list[str] = []
        for item in self.walk():
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, Template):
                parts.append(str(item))
        return "".join(parts)

    def __str__(self) -> str:
        return self.render()

    def __replace__(self, /, **changes):
        new_obj = type(self)()
        new_children = changes.get("children", self.children)

        if new_children:
            for child in new_children:
                if isinstance(child, Node):
                    new_obj.append_child(copy.replace(child))
                else:
                    new_obj.children.append(child)

        return new_obj

    def __iter__(self) -> Iterator[ChildNode]:
        """Iterate over direct children of this node."""
        return iter(self.children)

    def walk(self) -> Iterator[ChildNode]:
        """Depth-first traversal of this node and all descendants."""
        yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.walk()
            else:
                yield child

    def _validate_new_child(self, child: Node) -> None:
        if child is self:
            raise ValueError("Can't make a node a child of itself")
        if not isinstance(child, Node):
            raise ValueError(f"Expected a Node, str, or Template. Got {child.__class__.__name__!r}")
        if child.parent_node is not None:
            raise ValueError(f"Child {child!r} is already in the tree. Parent: {child.parent_node!r}")

    def append_child(self, child: ChildNode) -> None:
        """Add a child node to this node."""
        if isinstance(child, str | Template):
            self.children.append(child)
            return
        self._validate_new_child(child)
        child.parent_node = self
        self.children.append(child)

    def remove_child(self, child: ChildNode) -> None:
        """Remove a child node from this node."""
        if child not in self.children:
            raise ValueError(f"Node {child!r} is not a child of this node {self!r}")

        self.children.remove(child)
        if isinstance(child, Node):
            child.parent_node = None

    def insert_before(self, new_child: ChildNode, reference: ChildNode) -> None:
        """Insert new_child before reference in this node's children."""
        if isinstance(new_child, Node):
            self._validate_new_child(new_child)
        if reference not in self.children:
            raise ValueError(f"Reference node {reference!r} is not a child of this node")

        idx = self.children.index(reference)
        if isinstance(new_child, Node):
            new_child.parent_node = self
        self.children.insert(idx, new_child)

    def replace_child(self, new_child: ChildNode, old_child: ChildNode) -> ChildNode:
        """Replace old_child with new_child. Returns old_child."""
        if isinstance(new_child, Node):
            self._validate_new_child(new_child)
        if old_child not in self.children:
            raise ValueError(f"Node {old_child!r} is not a child of this node")

        idx = self.children.index(old_child)
        if isinstance(old_child, Node):
            old_child.parent_node = None
        if isinstance(new_child, Node):
            new_child.parent_node = self
        self.children[idx] = new_child
        return old_child

    def remove(self) -> None:
        """Remove this node from its parent."""
        if self.parent_node is None:
            raise ValueError("Cannot remove a node that has no parent")
        self.parent_node.remove_child(self)

    def _insert_nodes(self, parent: Node, idx: int, nodes: tuple[Node, ...]) -> None:
        for offset, node in enumerate(nodes):
            self._validate_new_child(node)
            node.parent_node = parent
            parent.children.insert(idx + offset, node)

    def replace_with(self, *nodes: Node) -> None:
        """Replace this node in its parent with one or more nodes."""
        if self.parent_node is None:
            raise ValueError("Cannot replace a node that has no parent")

        parent = self.parent_node
        idx = parent.children.index(self)
        self.parent_node = None
        parent.children.pop(idx)
        self._insert_nodes(parent, idx, nodes)

    def before(self, *nodes: Node) -> None:
        """Insert nodes before this node in its parent."""
        if self.parent_node is None:
            raise ValueError("Cannot insert before a node that has no parent")

        parent = self.parent_node
        idx = parent.children.index(self)
        self._insert_nodes(parent, idx, nodes)

    def after(self, *nodes: Node) -> None:
        """Insert nodes after this node in its parent."""
        if self.parent_node is None:
            raise ValueError("Cannot insert after a node that has no parent")

        parent = self.parent_node
        idx = parent.children.index(self) + 1
        self._insert_nodes(parent, idx, nodes)

    def prepend(self, *nodes: Node) -> None:
        """Insert nodes at the beginning of this node's children."""
        self._insert_nodes(self, 0, nodes)

    def contains(self, node: ChildNode) -> bool:
        """Check if node is a descendant of this node."""
        return any(descendant is node for descendant in self.walk())

    @property
    def first_child(self) -> ChildNode | None:
        """The first child of this node, or None if it has no children."""
        if self.children:
            return self.children[0]
        return None

    @property
    def last_child(self) -> ChildNode | None:
        """The last child of this node, or None if it has no children."""
        if self.children:
            return self.children[-1]
        return None

    @property
    def next_sibling(self) -> Node | None:
        """The next sibling of this node, or None if it has no next sibling."""
        if self.parent_node is None:
            return None

        siblings = self.parent_node.children
        index = siblings.index(self)
        if index + 1 < len(siblings):
            sibling = siblings[index + 1]
            return sibling if isinstance(sibling, Node) else None
        return None

    @property
    def previous_sibling(self) -> Node | None:
        """The previous sibling of this node, or None if it has no previous sibling."""
        if self.parent_node is None:
            return None

        siblings = self.parent_node.children
        index = siblings.index(self)
        if index - 1 >= 0:
            sibling = siblings[index - 1]
            return sibling if isinstance(sibling, Node) else None
        return None

    def clone_node(self, deep: bool = False) -> Self:
        """Clone this node. If deep=True, clone all descendants too."""
        if deep:
            return copy.replace(self)
        return copy.replace(self, children=[])


# Filled in by element.py at import time to avoid circular imports.
_Fragment: type[Fragment] | None = None
