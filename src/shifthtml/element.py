from __future__ import annotations

import copy
from collections.abc import Callable, Generator, Iterable, Iterator, Sequence
from typing import Any, ClassVar, Never, overload

from .compat import Template
from .node import Node as DOMNode
from .node import Element as DOMElement
from .node import Text as DOMText
from .render import render_attributes, render_string
from .types import NodeContent, NodeListContent


def _maybe_call[T](item: Callable[[], T] | T) -> T:
    if callable(item):
        return item()
    return item


def _copy_tree(old_node: DOMNode, pointer_target: DOMNode) -> tuple[DOMNode, DOMNode | None]:
    pointer_found: DOMNode | None = None

    new_node = copy.replace(old_node, children=[])

    if old_node is pointer_target:
        pointer_found = new_node

    for child in old_node.children:
        new_child, child_pointer = _copy_tree(child, pointer_target)
        new_node.append_child(new_child)
        if child_pointer is not None:
            pointer_found = child_pointer

    return new_node, pointer_found


class Fragment:
    """
    A document fragment that can contain nodes and other fragments.
    Not a DOM node — a builder wrapper around a DOM tree.
    """

    root: DOMNode
    append_pointer: DOMNode

    def __init__(self, root: DOMNode, append_pointer: DOMNode, /, **kwargs: Any):
        self.root = root
        self.append_pointer = append_pointer
        self.deferred: list[DeferredNode] = []

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
        return "".join(self)

    def __iter__(self) -> Iterator[str]:
        yield from self.render()

    @overload
    def __rshift__(self, other: None) -> None: ...

    @overload
    def __rshift__(self, other: NodeContent | Fragment) -> Fragment: ...

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

    def append(self, node: DOMNode | Fragment) -> None:
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

    def defer_node(self, node: DeferredNode) -> None:
        self.deferred.append(node)

    def render(self, *, defer_callback: Callable[[DeferredNode], None] | None = None) -> Generator[str]:
        if defer_callback is None:
            defer_callback = self.defer_node
        yield from self.root.render(defer_callback=defer_callback)
        yield from self.render_deferred_nodes()

    def render_deferred_nodes(self) -> Generator[str]:
        while len(self.deferred) > 0:
            node = self.deferred.pop(0)
            yield from node.render_result(defer_callback=self.defer_node)


class Node(DOMNode):
    """
    A node in the document tree with builder support.

    Extends the DOM Node with the >> operator for building HTML trees,
    and a factory method for creating nodes from various content types.
    """

    @classmethod
    def factory(cls, contents: NodeContent) -> Node:
        if isinstance(contents, Node):
            resolved = contents
        elif isinstance(contents, (str | Template)):
            resolved = Text(contents)
        elif isinstance(contents, Iterable):
            resolved = NodeList(contents)
        else:
            raise ValueError(f"Unsupported shift type for >>: {type(contents)}")

        return resolved

    @overload
    def __rshift__(self, other: NodeContent | Fragment) -> Fragment: ...

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

    def render(self, *, defer_callback: Callable[[DeferredNode], None] | None = None) -> Generator[str]:
        """Render the node to a string"""
        for child in self.children:
            yield from child.render(defer_callback=defer_callback)


class NodeList(Node, Sequence[DOMNode]):
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
    def __getitem__(self, index: int) -> DOMNode: ...

    @overload
    def __getitem__(self, index: slice[Any, Any, Any]) -> Sequence[DOMNode]: ...

    def __getitem__(self, index):
        return self.children[index]

    def __len__(self) -> int:
        return len(self.children)

    def __iter__(self) -> Iterator[DOMNode]:
        return iter(self.children)

    def __contains__(self, item: object) -> bool:
        return item in self.children

    def __reversed__(self) -> Iterator[DOMNode]:
        return reversed(self.children)

    def count(self, value: DOMNode) -> int:
        """Count occurrences of a value in the NodeList."""
        return self.children.count(value)

    def index(self, value: DOMNode, start: int = 0, stop: int | None = None) -> int:
        if stop is None:
            return self.children.index(value, start)
        return self.children.index(value, start, stop)


class Text(Node, DOMText):
    content: str | Template

    def __init__(self, content: str | Template, /, **kwargs: Any):
        super().__init__(content)

    def __repr__(self):
        return f"Text({self.content!r})"

    def __replace__(self, **changes):
        new_obj = type(self)(self.content)

        return new_obj

    def render(self, *, defer_callback: Callable[[DeferredNode], None] | None = None) -> Generator[str]:
        yield from render_string(self.content)


def _convert_attribute_names(name: str) -> str:
    if name == "classname":
        return "class"

    return name.replace("_", "-")


class Element(Node, DOMElement):
    tag: ClassVar[str]
    attributes: dict[str, str | Template]

    def __init__(self, attributes: dict[str, str | Template] | None = None, /, **keyword_attributes: str | Template):
        merged = attributes or {}
        merged.update({_convert_attribute_names(key): value for key, value in keyword_attributes.items()})
        super().__init__(tag_name=type(self).tag, attributes=merged)

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


class HTMLElement(Element):
    def render(self, *, defer_callback: Callable[[DeferredNode], None] | None = None) -> Generator[str]:
        if self.attributes:
            yield f"<{self.tag}"
            for attr in render_attributes(self.attributes):
                # space before each attribute
                yield f" {attr}"

            yield ">"
        else:
            yield f"<{self.tag}>"

        yield from super().render(defer_callback=defer_callback)

        yield f"</{self.tag}>"


class HTMLVoidElement(HTMLElement):
    def __repr__(self):
        return f"HTMLVoidElement({self.tag!r}, {self.attributes!r})"

    def __rshift__(self, other):
        raise ValueError(f"Cannot add children to a VoidElement ({self.tag})")

    def render(self, *, defer_callback: Callable[[DeferredNode], None] | None = None) -> Generator[str]:
        if self.attributes:
            yield f"<{self.tag}"
            for attr in render_attributes(self.attributes):
                # space before each attribute
                yield f" {attr}"

            yield " />"
        else:
            yield f"<{self.tag} />"


class DeferredNode(Node):
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
            raise ValueError(f"DeferredNode can only be initialized with a Node or Fragment, not {type(child)}")

    def __replace__(self, /, **changes):
        new_obj = type(self)(copy.replace(self.children[0]), slot_name=self.slot_name, loading=self.loading_node)

        return new_obj

    def render(self, *, defer_callback: Callable[[DeferredNode], None] | None = None) -> Generator[str]:
        # Render the loading message
        if defer_callback is None:
            raise ValueError("Deferred node rendered outside of Fragment")

        defer_callback(self)

        yield f'<template shadowrootmode="open"><slot name="{self.slot_name}">'
        if self.loading_node is not None:
            yield from self.loading_node.render(defer_callback=defer_callback)
        yield "</slot></template>"

    def render_result(self, *, defer_callback: Callable[[DeferredNode], None] | None = None) -> Generator[str]:
        if isinstance(self.children[0], HTMLElement):
            self.children[0].attributes["slot"] = self.slot_name
        yield from self.children[0].render(defer_callback=defer_callback)
