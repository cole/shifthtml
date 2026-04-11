from __future__ import annotations

import copy
from collections.abc import AsyncGenerator, Generator, Iterable, Iterator
from string.templatelib import Template
from typing import ClassVar, Literal, NoReturn, overload

from . import tree as _tree_module
from .errors import RenderLimitExceeded
from .lazy import Lazy
from .mappings import ClassList, DatasetMap, StyleMap, _snake_to_kebab
from .rendering import (
    RenderContext,
    aflush_deferred,
    astream_children,
    flush_deferred,
    render_open_tag,
    stream_children,
)
from .tree import Node
from .types import NodeContent, is_content_fn

_FLATTEN_MAX_DEPTH = 100


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


_attr_name_cache: dict[str, str] = {}


def _convert_attribute_names(name: str) -> str:
    try:
        return _attr_name_cache[name]
    except KeyError:
        result = _snake_to_kebab(name.rstrip("_"))
        _attr_name_cache[name] = result
        return result


# -- Fragment --


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

    def _chunks(self, ctx: RenderContext | None = None) -> Generator[str]:
        yield from self.root._chunks(ctx)

    async def _achunks(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        async for chunk in self.root._achunks(ctx):
            yield chunk

    def _collect(self, buf: list[str]) -> None:
        self.root._collect(buf)

    def __str__(self) -> str:
        buf: list[str] = []
        self.root._collect(buf)
        return "".join(buf)

    def __iter__(self) -> Iterator[Node | str | Template]:
        return iter(self.root.children)

    @overload
    def __rshift__(self, other: None) -> None: ...

    @overload
    def __rshift__(self, other: Literal[False]) -> None: ...

    @overload
    def __rshift__(self, other: NodeContent) -> Fragment: ...

    def __rshift__(self, other):
        if other is None or other is False:
            return None

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


# Register Fragment so tree.Node.__rshift__ can create instances without circular imports.
_tree_module._Fragment = Fragment


class Comment(Node):
    """An HTML comment node."""

    __slots__ = ("content",)

    content: str | Template

    def __init__(self, content: str | Template, /):
        self.parent_node = None
        self.children = []
        self.content = content

    def __repr__(self):
        return f"Comment({self.content!r})"

    def __replace__(self, **changes):
        return type(self)(self.content)

    def append_child(self, child):
        raise ValueError("Cannot add children to a Comment node")

    def _escape_content(self) -> str:
        content = str(self.content)
        return content.replace("--", "- -")

    def _chunks(self, ctx: RenderContext | None = None) -> Generator[str]:
        yield f"<!--{self._escape_content()}-->"

    async def _achunks(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        yield f"<!--{self._escape_content()}-->"


class Element(Node):
    """An HTML Element with tag, attributes, and builder support."""

    __slots__ = ("attributes", "_style", "_class_list", "_dataset")

    tag: ClassVar[str]
    _close_tag: ClassVar[str] = ""

    void: ClassVar[bool] = False
    doctype: ClassVar[str] = ""
    attributes: dict[str, object]

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "tag"):
            cls._close_tag = f"</{cls.tag}>"

    def __init__(self, attributes: dict[str, object] | None = None, /, **keyword_attributes: object):
        self.parent_node = None
        self.children = []
        if keyword_attributes:
            if attributes:
                merged: dict[str, object] = {k.lower(): v for k, v in attributes.items()}
                for k, v in keyword_attributes.items():
                    merged[_convert_attribute_names(k)] = v
                self.attributes = merged
            elif len(keyword_attributes) == 1:
                (k,) = keyword_attributes
                try:
                    attr_name = _attr_name_cache[k]
                except KeyError:
                    attr_name = _convert_attribute_names(k)
                self.attributes = {attr_name: keyword_attributes[k]}
            else:
                self.attributes = {_convert_attribute_names(k): v for k, v in keyword_attributes.items()}
        elif attributes:
            self.attributes = {k.lower(): v for k, v in attributes.items()}
        else:
            self.attributes = {}
        self._style = None
        self._class_list = None
        self._dataset = None

    def __repr__(self):
        return f"{type(self)}({self.tag!r}, {self.attributes!r})"

    def __replace__(self, /, **changes):
        new_obj = object.__new__(type(self))
        new_obj.parent_node = None
        new_obj.attributes = {**self.attributes}
        new_obj._style = None
        new_obj._class_list = None
        new_obj._dataset = None
        new_children = changes.get("children", self.children)
        if new_children:
            new_obj.children = []
            for child in new_children:
                if isinstance(child, Node):
                    new_obj.append_child(copy.replace(child))
                else:
                    new_obj.children.append(child)
        else:
            new_obj.children = []
        return new_obj

    def __getitem__(self, name: str) -> object:
        return self.attributes[name.lower()]

    def __setitem__(self, name: str, value: object) -> None:
        self.attributes[name.lower()] = value

    def __delitem__(self, name: str) -> None:
        del self.attributes[name.lower()]

    def __contains__(self, name: object) -> bool:
        if not isinstance(name, str):
            return False
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

    def _render_attrs(self) -> dict[str, object]:
        if self._style:
            return {**self.attributes, "style": self._style.css_text}
        return self.attributes

    def _chunks(self, ctx: RenderContext | None = None) -> Generator[str]:
        attrs = self._render_attrs()
        if self.void:
            yield render_open_tag(self.tag, attrs, void=True)
        else:
            if self.doctype:
                yield self.doctype
            yield render_open_tag(self.tag, attrs)
            yield from stream_children(self.children, ctx)
            if ctx is not None and ctx._deferred and self._is_flush_target(ctx):
                yield from flush_deferred(ctx)
            yield self._close_tag

    async def _achunks(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        attrs = self._render_attrs()
        if self.void:
            yield render_open_tag(self.tag, attrs, void=True)
        else:
            if self.doctype:
                yield self.doctype
            yield render_open_tag(self.tag, attrs)
            async for chunk in astream_children(self.children, ctx):
                yield chunk
            if ctx is not None and ctx._deferred and self._is_flush_target(ctx):
                async for chunk in aflush_deferred(ctx):
                    yield chunk
            yield self._close_tag

    def _is_flush_target(self, ctx: RenderContext) -> bool:
        """True when this is the root element (flush deferred before close tag)."""
        return self is ctx._root_node


class VoidElement(Element):
    """An HTML element that cannot have children (e.g., img, br, input)."""

    __slots__ = ()

    void: ClassVar[bool] = True

    def append_child(self, child: object) -> NoReturn:
        raise ValueError(f"Cannot add children to a void element ({self.tag})")

    def __rshift__(self, other: object) -> NoReturn:
        raise ValueError(f"Cannot add children to a void element ({self.tag})")
