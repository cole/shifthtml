from __future__ import annotations

import copy
from collections.abc import Callable, Generator, Iterable, Iterator, Sequence
from string.templatelib import Template
from typing import Any, ClassVar, overload

from .mappings import ClassList, DatasetMap, StyleMap, _snake_to_kebab
from .node import Node as _Node
from .render import render_attributes, render_string
from .types import NodeContent, NodeListContent


def _maybe_call[T](item: Callable[[], T] | T) -> T:
    if callable(item):
        return item()  # type: ignore[call-top-callable]  # ty can't narrow Callable[[], T] | T when T itself may be callable
    return item


def _copy_tree(old_node: _Node, pointer_target: _Node) -> tuple[_Node, _Node | None]:
    pointer_found: _Node | None = None

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

    root: _Node
    append_pointer: _Node

    def __init__(self, root: _Node, append_pointer: _Node, /, **kwargs: Any):
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

    def __iter__(self) -> Iterator[_Node]:
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

    def append(self, node: _Node | Fragment) -> None:
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


class Node(_Node):
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


class NodeList(Node, Sequence[_Node]):
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
    def __getitem__(self, index: int) -> _Node: ...

    @overload
    def __getitem__(self, index: slice[Any, Any, Any]) -> Sequence[_Node]: ...

    def __getitem__(self, index):
        return self.children[index]

    def __len__(self) -> int:
        return len(self.children)

    def __iter__(self) -> Iterator[_Node]:
        return iter(self.children)

    def __contains__(self, item: object) -> bool:
        return item in self.children

    def __reversed__(self) -> Iterator[_Node]:
        return reversed(self.children)

    def count(self, value: _Node) -> int:
        """Count occurrences of a value in the NodeList."""
        return self.children.count(value)

    def index(self, value: _Node, start: int = 0, stop: int | None = None) -> int:
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


class Element(Node):
    """An HTML Element with tag, attributes, and builder support."""

    tag: ClassVar[str]
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

    def get_attribute(self, name: str) -> str | Template | None:
        return self.attributes.get(name.lower())

    def set_attribute(self, name: str, value: str | Template) -> None:
        self.attributes[name.lower()] = value

    def has_attribute(self, name: str) -> bool:
        return name.lower() in self.attributes

    def remove_attribute(self, name: str) -> None:
        self.attributes.pop(name.lower(), None)

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
            existing = self.get_attribute("style")
            if existing and isinstance(existing, str):
                self._style.css_text = existing
                self.remove_attribute("style")
        return self._style


class HTMLElement(Element):
    def render(self, *, defer_callback: Callable[[Deferred], None] | None = None) -> Generator[str]:
        if self._style:
            self.set_attribute("style", self._style.css_text)

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

    def render(self, *, defer_callback: Callable[[Deferred], None] | None = None) -> Generator[str]:
        if self.attributes:
            yield f"<{self.tag}"
            for attr in render_attributes(self.attributes):
                # space before each attribute
                yield f" {attr}"

            yield " />"
        else:
            yield f"<{self.tag} />"


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
        if isinstance(self.children[0], HTMLElement):
            self.children[0].set_attribute("slot", self.slot_name)
        yield from self.children[0].render(defer_callback=defer_callback)
