from __future__ import annotations

import copy
import inspect
from collections.abc import AsyncGenerator, Awaitable, Callable, Generator, Iterable, Iterator, Sequence
from string.templatelib import Template
from typing import Any, ClassVar, NoReturn, overload

import anyio

from .mappings import ClassList, DatasetMap, StyleMap, _snake_to_kebab
from .render import render_attributes, render_string
from .tree import TreeNode
from .types import NodeContent, NodeListContent


def _maybe_call[T](item: Callable[[], T] | T) -> T:
    if callable(item) and not inspect.iscoroutinefunction(item):
        return item()  # type: ignore[call-top-callable]  # ty can't narrow Callable[[], T] | T when T itself may be callable
    return item  # type: ignore[invalid-return-type]  # async callables are passed through unchanged


def _copy_tree(old_node: TreeNode, pointer_target: TreeNode) -> tuple[TreeNode, TreeNode | None]:
    pointer_found: TreeNode | None = None

    new_node = copy.replace(old_node, children=[])

    if old_node is pointer_target:
        pointer_found = new_node

    for child in old_node.children:
        new_child, child_pointer = _copy_tree(child, pointer_target)
        new_node.append_child(new_child)
        if child_pointer is not None:
            pointer_found = child_pointer

    return new_node, pointer_found


def _convert_attribute_names(name: str) -> str:
    if name == "classname":
        return "class"
    return _snake_to_kebab(name)


class Fragment:
    """
    A document fragment that can contain nodes and other fragments.
    Not a DOM node — a builder wrapper around a DOM tree.
    """

    root: TreeNode
    append_pointer: TreeNode

    def __init__(self, root: TreeNode, append_pointer: TreeNode, /, **kwargs: Any):
        self.root = root
        self.append_pointer = append_pointer
        self.deferred: list[Deferred] = []

    def __copy__(self) -> Fragment:
        return Fragment(self.root, self.append_pointer)

    def __deepcopy__(self, memo=None) -> Fragment:
        new_root, new_pointer = _copy_tree(self.root, self.append_pointer)
        if new_pointer is None:
            raise ValueError("Pointer target not found in the tree")
        return Fragment(new_root, new_pointer)

    def __replace__(self, /, **changes):
        new_root, new_pointer = _copy_tree(self.root, self.append_pointer)
        if new_pointer is None:
            raise ValueError("Pointer target not found in the tree")
        return Fragment(new_root, new_pointer)

    def __repr__(self):
        return f"Fragment({self.root!r}, {self.append_pointer!r})"

    def __str__(self):
        return "".join(self.render())

    def __iter__(self) -> Iterator[TreeNode]:
        return iter(self.root.children)

    @overload
    def __rshift__(self, other: None) -> None: ...

    @overload
    def __rshift__(self, other: NodeContent) -> Fragment: ...

    def __rshift__(self, other):
        resolved = _maybe_call(other)

        if resolved is None:
            return None

        if isinstance(resolved, Fragment):
            new_fragment = copy.replace(self)
            new_fragment.append(copy.replace(resolved))
            return new_fragment

        node = Node.factory(resolved)
        self.append(node)

        return self

    def append(self, node: TreeNode | Fragment) -> None:
        """Modify the tree by appending a node to the end."""
        if isinstance(node, Fragment):
            new_root, new_pointer = _copy_tree(node.root, node.append_pointer)
            if new_pointer is None:
                raise ValueError("Pointer target not found in the tree")
            self.append_pointer.append_child(new_root)
            self.append_pointer = new_pointer
            return

        self.append_pointer.append_child(node)
        self.append_pointer = node

    def defer_node(self, node: Deferred) -> None:
        self.deferred.append(node)

    def render(self, *, defer_callback: Callable[[Deferred], None] | None = None) -> Generator[str]:
        if defer_callback is None:
            defer_callback = self.defer_node
        yield from self.root.render(defer_callback=defer_callback)
        yield from self.render_deferred_nodes()

    def render_deferred_nodes(self) -> Generator[str]:
        while len(self.deferred) > 0:
            node = self.deferred.pop(0)
            yield from node.render_result(defer_callback=self.defer_node)

    async def arender(self, *, defer_callback: Callable[[Deferred], None] | None = None) -> AsyncGenerator[str]:
        if defer_callback is None:
            defer_callback = self.defer_node
        async for chunk in self.root.arender(defer_callback=defer_callback):
            yield chunk
        async for chunk in self.arender_deferred_nodes():
            yield chunk

    async def arender_deferred_nodes(self) -> AsyncGenerator[str]:
        while len(self.deferred) > 0:
            node = self.deferred.pop(0)
            async for chunk in node.arender_result(defer_callback=self.defer_node):
                yield chunk


class Node(TreeNode):
    """
    A node in the document tree with builder support.

    Extends the abstract Node with the >> operator for building HTML trees,
    and a factory method for creating nodes from various content types.
    """

    @classmethod
    def factory(cls, contents: NodeContent) -> Node:
        if isinstance(contents, Node):
            return contents
        if isinstance(contents, Fragment):
            return NodeList([contents])
        if isinstance(contents, str | Template):
            return Text(contents)
        if callable(contents):
            if inspect.iscoroutinefunction(contents):
                return Async(contents)
            return cls.factory(contents())  # type: ignore[call-top-callable]
        if isinstance(contents, Iterable):
            return NodeList(contents)
        raise ValueError(f"Unsupported shift type for >>: {type(contents)}")

    @overload
    def __rshift__(self, other: NodeContent) -> Fragment: ...

    @overload
    def __rshift__(self, other: None) -> None: ...

    def __rshift__(self, other):
        resolved = _maybe_call(other)

        if resolved is None:
            return None

        new_fragment = Fragment(self, self)

        if isinstance(resolved, Fragment):
            new_fragment.append(resolved)
            return new_fragment

        node = Node.factory(resolved)
        new_fragment.append(node)

        return new_fragment

    @property
    def text_content(self) -> str:
        """Get the text content of this node and all descendants."""
        parts: list[str] = []
        for node in self.walk():
            if isinstance(node, Text):
                content = node.content
                parts.append(str(content) if not isinstance(content, str) else content)
        return "".join(parts)

    def __str__(self) -> str:
        return "".join(self.render())

    def render(self, *, defer_callback: Callable[[Deferred], None] | None = None) -> Generator[str]:
        """Render the node to a string"""
        for child in self.children:
            yield from child.render(defer_callback=defer_callback)

    async def arender(self, *, defer_callback: Callable[[Deferred], None] | None = None) -> AsyncGenerator[str]:
        """Async rendering with parallel sibling resolution."""
        results: list[list[str]] = [[] for _ in self.children]

        async def collect(i: int, child: TreeNode) -> None:
            results[i] = [chunk async for chunk in child.arender(defer_callback=defer_callback)]

        async with anyio.create_task_group() as tg:
            for i, child in enumerate(self.children):
                tg.start_soon(collect, i, child)

        for chunks in results:
            for chunk in chunks:
                yield chunk


class NodeList(Node, Sequence[TreeNode]):
    """A list of nodes with a position in the tree."""

    def __init__(self, contents: NodeListContent, /, **kwargs):
        super().__init__()

        for item in contents:
            if item is None:
                continue

            item = _maybe_call(item)

            if isinstance(item, Fragment):
                self.append_child(item.root)
            else:
                item_node = Node.factory(item)
                if item_node is not None:
                    self.append_child(item_node)

    def __repr__(self):
        return f"NodeList({repr(self.children)})"

    @overload
    def __getitem__(self, index: int) -> TreeNode: ...

    @overload
    def __getitem__(self, index: slice[Any, Any, Any]) -> Sequence[TreeNode]: ...

    def __getitem__(self, index):
        return self.children[index]

    def __len__(self) -> int:
        return len(self.children)

    def __iter__(self) -> Iterator[TreeNode]:
        return iter(self.children)

    def __contains__(self, item: object) -> bool:
        return item in self.children

    def __reversed__(self) -> Iterator[TreeNode]:
        return reversed(self.children)

    def count(self, value: TreeNode) -> int:
        """Count occurrences of a value in the NodeList."""
        return self.children.count(value)

    def index(self, value: TreeNode, start: int = 0, stop: int | None = None) -> int:
        if stop is None:
            return self.children.index(value, start)
        return self.children.index(value, start, stop)


class Text(Node):
    """An HTML Text Node."""

    content: str | Template

    def __init__(self, content: str | Template, /, **kwargs: Any):
        super().__init__()
        self.content = content

    def __repr__(self):
        return f"Text({self.content!r})"

    def __replace__(self, **changes):
        return type(self)(self.content)

    def append_child(self, child):
        raise ValueError("Cannot add children to a Text node")

    def render(self, *, defer_callback: Callable[[Deferred], None] | None = None) -> Generator[str]:
        yield from render_string(self.content)

    async def arender(self, *, defer_callback: Callable[[Deferred], None] | None = None) -> AsyncGenerator[str]:
        from .arender import arender_string

        async for chunk in arender_string(self.content):
            yield chunk


class Comment(Node):
    """An HTML Comment Node."""

    content: str | Template

    def __init__(self, content: str | Template, /, **kwargs: Any):
        super().__init__()
        self.content = content

    def __repr__(self):
        return f"Comment({self.content!r})"

    def __replace__(self, **changes):
        return type(self)(self.content)

    def append_child(self, child):
        raise ValueError("Cannot add children to a Comment node")

    def render(self, *, defer_callback: Callable[[Deferred], None] | None = None) -> Generator[str]:
        yield f"<!--{self.content}-->"

    async def arender(self, *, defer_callback: Callable[[Deferred], None] | None = None) -> AsyncGenerator[str]:
        yield f"<!--{self.content}-->"


class Element(Node):
    """An HTML Element with tag, attributes, and builder support."""

    tag: ClassVar[str]
    void: ClassVar[bool] = False
    attributes: dict[str, str | Template]

    def __init__(self, attributes: dict[str, str | Template] | None = None, /, **keyword_attributes: str | Template):
        super().__init__()
        merged: dict[str, str | Template] = {k.lower(): v for k, v in attributes.items()} if attributes else {}
        merged.update({_convert_attribute_names(key): value for key, value in keyword_attributes.items()})
        self._tag_name = type(self).tag
        self._style: StyleMap | None = None
        self._class_list: ClassList | None = None
        self._dataset: DatasetMap | None = None
        self.attributes = merged

    def __repr__(self):
        return f"{type(self)}({self.tag!r}, {self.attributes!r})"

    def __replace__(self, /, **changes):
        new_obj = type(self)()
        new_obj.attributes = dict(self.attributes)
        new_children = changes.get("children", self.children)
        if new_children:
            for child in new_children:
                new_obj.append_child(copy.replace(child))
        return new_obj

    @property
    def tag_name(self) -> str:
        """The tag name of this element."""
        return self._tag_name

    def __getitem__(self, name: str) -> str | Template:
        return self.attributes[name.lower()]

    def __setitem__(self, name: str, value: str | Template) -> None:
        self.attributes[name.lower()] = value

    def __delitem__(self, name: str) -> None:
        del self.attributes[name.lower()]

    def __contains__(self, name: object) -> bool:
        if not isinstance(name, str):
            return NotImplemented
        return name.lower() in self.attributes

    @property
    def dataset(self) -> DatasetMap:
        if self._dataset is None:
            self._dataset = DatasetMap(owner=self)
        return self._dataset

    @property
    def class_list(self) -> ClassList:
        if self._class_list is None:
            self._class_list = ClassList(owner=self)
        return self._class_list

    @property
    def style(self) -> StyleMap:
        if self._style is None:
            self._style = StyleMap(owner=self)
            existing = self.attributes.get("style")
            if existing and isinstance(existing, str):
                self._style.css_text = existing
                del self["style"]
        return self._style

    def render(self, *, defer_callback: Callable[[Deferred], None] | None = None) -> Generator[str]:
        if self._style:
            self["style"] = self._style.css_text

        if self.attributes:
            yield f"<{self.tag}"
            for attr in render_attributes(self.attributes):
                yield f" {attr}"
        else:
            yield f"<{self.tag}"

        if self.void:
            yield " />"
        else:
            yield ">"
            for child in self.children:
                yield from child.render(defer_callback=defer_callback)
            yield f"</{self.tag}>"

    async def arender(self, *, defer_callback: Callable[[Deferred], None] | None = None) -> AsyncGenerator[str]:
        if self._style:
            self["style"] = self._style.css_text

        if self.attributes:
            yield f"<{self.tag}"
            for attr in render_attributes(self.attributes):
                yield f" {attr}"
        else:
            yield f"<{self.tag}"

        if self.void:
            yield " />"
        else:
            yield ">"

            results: list[list[str]] = [[] for _ in self.children]

            async def collect(i: int, child: TreeNode) -> None:
                results[i] = [chunk async for chunk in child.arender(defer_callback=defer_callback)]

            async with anyio.create_task_group() as tg:
                for i, child in enumerate(self.children):
                    tg.start_soon(collect, i, child)

            for chunks in results:
                for chunk in chunks:
                    yield chunk

            yield f"</{self.tag}>"


class VoidElement(Element):
    """An HTML element that cannot have children (e.g., img, br, input)."""

    void: ClassVar[bool] = True

    def append_child(self, child: object) -> NoReturn:
        raise ValueError(f"Cannot add children to a void element ({self.tag})")

    def __rshift__(self, other: object) -> NoReturn:
        raise ValueError(f"Cannot add children to a void element ({self.tag})")


class Deferred(Node):
    def __init__(
        self,
        child: Node | Fragment,
        *,
        slot_name: str,
        loading: NodeContent | None = None,
    ):
        super().__init__()
        self.loading_node = Node.factory(loading) if loading is not None else None
        self.slot_name = slot_name

        if isinstance(child, Fragment):
            self.append_child(child.root)
        elif isinstance(child, Node):
            self.append_child(child)
        else:
            raise ValueError(f"Deferred can only be initialized with a Node or Fragment, not {type(child)}")

    def __replace__(self, /, **changes):
        new_obj = type(self)(copy.replace(self.children[0]), slot_name=self.slot_name, loading=self.loading_node)

        return new_obj

    def render(self, *, defer_callback: Callable[[Deferred], None] | None = None) -> Generator[str]:
        # Render the loading message
        if defer_callback is None:
            raise ValueError("Deferred node rendered outside of Fragment")

        defer_callback(self)

        yield f'<template shadowrootmode="open"><slot name="{self.slot_name}">'
        if self.loading_node is not None:
            yield from self.loading_node.render(defer_callback=defer_callback)
        yield "</slot></template>"

    def render_result(self, *, defer_callback: Callable[[Deferred], None] | None = None) -> Generator[str]:
        if isinstance(self.children[0], Element):
            self.children[0]["slot"] = self.slot_name
        yield from self.children[0].render(defer_callback=defer_callback)

    async def arender_result(self, *, defer_callback: Callable[[Deferred], None] | None = None) -> AsyncGenerator[str]:
        if isinstance(self.children[0], Element):
            self.children[0]["slot"] = self.slot_name
        async for chunk in self.children[0].arender(defer_callback=defer_callback):
            yield chunk

    async def arender(self, *, defer_callback: Callable[[Deferred], None] | None = None) -> AsyncGenerator[str]:
        if defer_callback is None:
            raise ValueError("Deferred node rendered outside of Fragment")

        defer_callback(self)

        yield f'<template shadowrootmode="open"><slot name="{self.slot_name}">'
        if self.loading_node is not None:
            async for chunk in self.loading_node.arender(defer_callback=defer_callback):
                yield chunk
        yield "</slot></template>"


class Async(Node):
    """Wraps an async callable, resolved during async rendering."""

    fn: Callable[[], Awaitable[NodeContent]]

    def __init__(self, fn: Callable[[], Awaitable[NodeContent]], /, **kwargs: Any):
        super().__init__()
        self.fn = fn

    def __repr__(self):
        return f"Async({self.fn!r})"

    def __replace__(self, **changes):
        return type(self)(self.fn)

    def render(self, *, defer_callback: Callable[[Deferred], None] | None = None) -> Generator[str]:
        raise TypeError("Async nodes require async rendering")

    async def arender(self, *, defer_callback: Callable[[Deferred], None] | None = None) -> AsyncGenerator[str]:
        result = await self.fn()
        node = Node.factory(result)
        async for chunk in node.arender(defer_callback=defer_callback):
            yield chunk
