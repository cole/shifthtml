"""
Abstract base class for nodes in a tree structure, analogous to DOM nodes.
"""

from __future__ import annotations

import copy
import inspect
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Awaitable, Callable, Generator, Iterable, Iterator
from contextvars import ContextVar
from string.templatelib import Template
from typing import Any, Self

from .errors import RenderLimitExceeded
from .rendering import (
    RenderContext,
    aflush_deferred,
    arender_result,
    astream_children,
    stream_children,
)
from .types import _MISSING, NodeContent, is_content_fn

_render_vars: ContextVar[dict[str, object] | None] = ContextVar("shifthtml.render_vars", default=None)

type ChildNode = Node | str | Template

_EMPTY_ARGS: dict[str, object] = {}

_FLATTEN_MAX_DEPTH = 100

_LAZY_TYPE_ERROR = (
    "Lazy nodes require async rendering. Use `await node.render()` or `async for chunk in node.stream()`."
)


def _resolve_var(name: str, default: object = _MISSING) -> Any:
    """Look up a render-time variable by name. Used by compiled template execution."""
    vars = _render_vars.get()
    if vars and name in vars:
        return vars[name]
    if default is not _MISSING:
        return default
    raise LookupError(f"Var {name!r} not set")


class Node(ABC):
    """
    Abstract base class for all nodes in the document tree.

    Analogous to the DOM Node interface. Manages parent/child relationships,
    provides tree traversal, and supports rendering to HTML via chunks()/achunks().

    The >> operator builds HTML trees in-place, returning self. The _cursor slot
    tracks where the next appended Node should land so chained ``a >> b >> c``
    nests into the tree rather than appending siblings.
    """

    __slots__ = ("parent_node", "children", "_cursor")

    parent_node: None | Node
    children: list[ChildNode]
    _cursor: Node | None

    def __init__(self):
        self.parent_node = None
        self.children = []
        self._cursor = None

    def _collect(self, buf: list[str]) -> None:
        """Collect HTML chunks into a buffer. Default delegates to chunks()."""
        buf.extend(self.chunks())

    @abstractmethod
    def chunks(self, ctx: RenderContext | None = None) -> Generator[str]:
        """Yield HTML chunks for this node."""
        ...

    @abstractmethod
    def achunks(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        """Yield HTML chunks asynchronously."""
        ...

    async def render(
        self,
        *,
        args: dict[str, object] | None = None,
        max_depth: int = 100,
        max_nodes: int | None = None,
    ) -> str:
        """Render this node to an HTML string."""
        _render_vars.set(args if args is not None else _EMPTY_ARGS)
        ctx = RenderContext(max_depth=max_depth, max_nodes=max_nodes, _root_node=self)
        parts: list[str] = []
        async for chunk in self.achunks(ctx):
            parts.append(chunk)
        async for chunk in aflush_deferred(ctx):
            parts.append(chunk)
        return "".join(parts)

    async def stream(
        self,
        *,
        args: dict[str, object] | None = None,
        max_depth: int = 100,
        max_nodes: int | None = None,
    ) -> AsyncGenerator[str]:
        """Yield HTML chunks asynchronously for this node."""
        _render_vars.set(args or {})
        ctx = RenderContext(max_depth=max_depth, max_nodes=max_nodes, _root_node=self)
        async for chunk in self.achunks(ctx):
            yield chunk
        async for chunk in aflush_deferred(ctx):
            yield chunk

    def __rshift__(self, other: NodeContent | None) -> Self:
        if other is None or other is False:
            return self

        target = self._cursor if self._cursor is not None else self

        if isinstance(other, Iterable) and not isinstance(other, str | Template | Node | Fragment):
            _flatten_into(target, other)
            return self

        child = normalize(other)
        if child is None:
            return self
        if isinstance(child, str | Template):
            target.children.append(child)
        else:
            if child.parent_node is not None:
                child = child.clone_node(deep=True)
            target.append_child(child)
            self._cursor = child
        return self

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
        buf: list[str] = []
        self._collect(buf)
        return "".join(buf)

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


class ContainerNode(Node):
    """Concrete node that renders only its children (no tag markup)."""

    __slots__ = ()

    def chunks(self, ctx: RenderContext | None = None) -> Generator[str]:
        yield from stream_children(self.children, ctx)

    async def achunks(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        async for chunk in astream_children(self.children, ctx):
            yield chunk


class Lazy(Node):
    """Wraps a zero-arg callable, resolved during rendering.

    Handles both sync and async callables. All Lazy nodes require async
    rendering — _collect and chunks raise TypeError. Use render() or stream().
    """

    __slots__ = ("fn", "_is_async")

    fn: Callable[..., object]
    _is_async: bool

    def __init__(self, fn: Callable[..., object], /):
        super().__init__()
        self.fn = fn
        self._is_async = inspect.iscoroutinefunction(fn)

    def __repr__(self) -> str:
        return f"Lazy({self.fn!r})"

    def __replace__(self, **changes: object) -> Lazy:
        return type(self)(self.fn)

    def _collect(self, buf: list[str]) -> None:
        raise TypeError(_LAZY_TYPE_ERROR)

    def chunks(self, ctx: RenderContext | None = None) -> Generator[str]:
        raise TypeError(_LAZY_TYPE_ERROR)
        yield  # unreachable, but makes this a generator function

    async def achunks(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        if ctx is not None:
            if ctx._depth >= ctx.max_depth:
                raise RenderLimitExceeded(f"Exceeded max render depth ({ctx.max_depth})")
            ctx._depth += 1
        result = self.fn()
        if isinstance(result, Awaitable):
            result = await result
        async for chunk in arender_result(result, ctx):
            yield chunk
        if ctx is not None:
            ctx._depth -= 1


def normalize(content: NodeContent) -> Node | str | Template | None:
    """Normalize any NodeContent value into a leaf type for tree insertion.

    Returns None for suppressed values (None, False).
    Strings and Templates pass through unchanged.
    Fragments are unwrapped to their root (cloned if already parented).
    Callables are wrapped as Lazy nodes.
    """
    if content is None or content is False:
        return None
    if isinstance(content, str | Template | Node):
        return content
    if isinstance(content, Fragment):
        root = content.root
        if root.parent_node is not None:
            return root.clone_node(deep=True)
        return root
    if is_content_fn(content):
        return Lazy(content)
    raise ValueError(f"Unsupported type: {type(content)}")


def _copy_tree(old_node: Node, pointer_target: Node) -> tuple[Node, Node | None]:
    pointer_found: Node | None = None

    new_node = old_node.__replace__(children=[])

    if old_node is pointer_target:
        pointer_found = new_node

    for child in old_node.children:
        if type(child) is str or isinstance(child, Template):
            new_node.children.append(child)
        elif isinstance(child, Node):
            new_child, child_pointer = _copy_tree(child, pointer_target)
            new_child.parent_node = new_node
            new_node.children.append(new_child)
            if child_pointer is not None:
                pointer_found = child_pointer

    return new_node, pointer_found


def _flatten_into(parent: Node, items: Iterable, *, _depth: int = 0) -> None:
    """Flatten an iterable of children directly into parent's children list."""
    if _depth > _FLATTEN_MAX_DEPTH:
        raise RenderLimitExceeded("Exceeded max nesting depth in children")
    children = parent.children
    for item in items:
        if isinstance(item, Iterable) and not isinstance(item, str | Template | Node | Fragment):
            _flatten_into(parent, item, _depth=_depth + 1)
            continue
        child = normalize(item)
        if child is None:
            continue
        if isinstance(child, Node):
            if child.parent_node is not None:
                child = child.clone_node(deep=True)
            child.parent_node = parent
        children.append(child)


class Fragment:
    """A document fragment — a builder wrapper around a DOM tree."""

    __slots__ = ("root", "append_pointer")

    root: Node
    append_pointer: Node

    def __init__(self, root: Node, append_pointer: Node, /):
        self.root = root
        self.append_pointer = append_pointer

    def __copy__(self) -> Fragment:
        return Fragment(self.root, self.append_pointer)

    def __deepcopy__(self, memo=None) -> Fragment:
        new_root, new_pointer = _copy_tree(self.root, self.append_pointer)
        if new_pointer is None:
            raise ValueError("Pointer target not found in the tree")
        return Fragment(new_root, new_pointer)

    def __replace__(self, /, **changes):
        return copy.deepcopy(self)

    def __repr__(self):
        return f"Fragment({self.root!r}, {self.append_pointer!r})"

    async def render(
        self,
        *,
        args: dict[str, object] | None = None,
        max_depth: int = 100,
        max_nodes: int | None = None,
    ) -> str:
        return await self.root.render(args=args, max_depth=max_depth, max_nodes=max_nodes)

    async def stream(
        self,
        *,
        args: dict[str, object] | None = None,
        max_depth: int = 100,
        max_nodes: int | None = None,
    ) -> AsyncGenerator[str]:
        async for chunk in self.root.stream(args=args, max_depth=max_depth, max_nodes=max_nodes):
            yield chunk

    def chunks(self, ctx: RenderContext | None = None) -> Generator[str]:
        yield from self.root.chunks(ctx)

    async def achunks(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        async for chunk in self.root.achunks(ctx):
            yield chunk

    def _collect(self, buf: list[str]) -> None:
        self.root._collect(buf)

    def __str__(self) -> str:
        buf: list[str] = []
        self.root._collect(buf)
        return "".join(buf)

    def __iter__(self) -> Iterator[Node | str | Template]:
        return iter(self.root.children)

    def __rshift__(self, other: NodeContent | None) -> Fragment:
        if other is None or other is False:
            return self

        if isinstance(other, Iterable) and not isinstance(other, str | Template | Node | Fragment):
            _flatten_into(self.append_pointer, other)
            return self

        child = normalize(other)
        if child is None:
            return self
        if isinstance(child, str | Template):
            self.append_pointer.children.append(child)
        else:
            self.append(child)
        return self

    def append(self, node: Node | Fragment) -> None:
        """Modify the tree by appending a node to the end."""
        if isinstance(node, Fragment):
            new_root, new_pointer = _copy_tree(node.root, node.append_pointer)
            if new_pointer is None:
                raise ValueError("Pointer target not found in the tree")
            # Skip validation — _copy_tree always produces a fresh unparented root
            new_root.parent_node = self.append_pointer
            self.append_pointer.children.append(new_root)
            self.append_pointer = new_pointer
            return

        self.append_pointer.append_child(node)
        self.append_pointer = node
