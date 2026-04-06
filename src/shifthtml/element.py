from __future__ import annotations

import copy
from collections.abc import AsyncGenerator, Awaitable, Callable, Generator, Iterable, Iterator
from contextlib import suppress
from string.templatelib import Template
from typing import TYPE_CHECKING, Any, ClassVar, Literal, NoReturn, overload

import anyio

from .errors import RenderLimitExceeded
from .mappings import ClassList, DatasetMap, StyleMap, _snake_to_kebab
from .rendering import (
    arender_result,
    astream_children,
    render_open_tag,
    render_result,
    stream_children,
)
from .rendering import astream as _astream_impl
from .rendering import render as _render_impl
from .rendering import stream as _stream_impl
from .tree import TreeNode, _render_vars
from .types import NodeContent, is_async_content_fn, is_sync_content_fn

if TYPE_CHECKING:
    from .plugin import Plugin, RenderContext

_FLATTEN_MAX_DEPTH = 100


def _copy_tree(old_node: TreeNode, pointer_target: TreeNode) -> tuple[TreeNode, TreeNode | None]:
    pointer_found: TreeNode | None = None

    new_node = copy.replace(old_node, children=[])

    if old_node is pointer_target:
        pointer_found = new_node

    for child in old_node.children:
        if isinstance(child, str | Template):
            new_node.children.append(child)
        else:
            new_child, child_pointer = _copy_tree(child, pointer_target)
            new_node.append_child(new_child)
            if child_pointer is not None:
                pointer_found = child_pointer

    return new_node, pointer_found


def _flatten_into(parent: TreeNode, items: Iterable, *, _depth: int = 0) -> None:
    """Flatten an iterable of children directly into parent's children list."""
    if _depth > _FLATTEN_MAX_DEPTH:
        raise RenderLimitExceeded("Exceeded max nesting depth in children")
    children = parent.children
    for item in items:
        if item is None or item is False:
            continue
        if isinstance(item, str | Template):
            children.append(item)
        elif isinstance(item, Fragment):
            root = item.root
            if root.parent_node is not None:
                root = root.clone_node(deep=True)
            root.parent_node = parent
            children.append(root)
        elif isinstance(item, Node):
            if item.parent_node is not None:
                item = item.clone_node(deep=True)
            item.parent_node = parent
            children.append(item)
        elif isinstance(item, Iterable):
            _flatten_into(parent, item, _depth=_depth + 1)
        else:
            node = Node.factory(item)
            node.parent_node = parent
            children.append(node)


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
        # _copy_tree preserves concrete types via copy.replace
        assert isinstance(new_root, Node)
        assert isinstance(new_pointer, Node)
        return Fragment(new_root, new_pointer)

    def __replace__(self, /, **changes):
        return copy.deepcopy(self)

    def __repr__(self):
        return f"Fragment({self.root!r}, {self.append_pointer!r})"

    def render(
        self,
        *,
        args: dict[str, object] | None = None,
        plugins: tuple[Plugin, ...] | None = None,
        max_depth: int = 100,
        max_nodes: int | None = None,
    ) -> str:
        return _render_impl(self, args=args, plugins=plugins, max_depth=max_depth, max_nodes=max_nodes)

    def stream(
        self,
        *,
        args: dict[str, object] | None = None,
        plugins: tuple[Plugin, ...] | None = None,
        max_depth: int = 100,
        max_nodes: int | None = None,
    ) -> Generator[str]:
        return _stream_impl(self, args=args, plugins=plugins, max_depth=max_depth, max_nodes=max_nodes)

    def astream(
        self,
        *,
        args: dict[str, object] | None = None,
        plugins: tuple[Plugin, ...] | None = None,
        min_chunk_size: int | None = 4096,
        cancel_scope: anyio.CancelScope | None = None,
        max_depth: int = 100,
        max_nodes: int | None = None,
    ) -> AsyncGenerator[str]:
        return _astream_impl(
            self,
            args=args,
            plugins=plugins,
            min_chunk_size=min_chunk_size,
            cancel_scope=cancel_scope,
            max_depth=max_depth,
            max_nodes=max_nodes,
        )

    def _stream(self, ctx: RenderContext | None = None) -> Generator[str]:
        yield from self.root._stream(ctx)

    async def _astream(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        async for chunk in self.root._astream(ctx):
            yield chunk

    def __str__(self):
        return self.render()

    def __iter__(self) -> Iterator[TreeNode | str | Template]:
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

        if isinstance(other, str | Template):
            self.append_pointer.children.append(other)
            return self

        if isinstance(other, tuple | list):
            _flatten_into(self.append_pointer, other)
            return self

        if isinstance(other, Fragment):
            self.append(other)
            return self

        if isinstance(other, Node):
            self.append(other)
            return self

        if isinstance(other, Iterable):
            _flatten_into(self.append_pointer, other)
            return self

        node = Node.factory(other)
        self.append(node)

        return self

    def append(self, node: Node | Fragment) -> None:
        """Modify the tree by appending a node to the end."""
        if isinstance(node, Fragment):
            new_root, new_pointer = _copy_tree(node.root, node.append_pointer)
            if new_pointer is None:
                raise ValueError("Pointer target not found in the tree")
            # _copy_tree preserves concrete types via copy.replace
            assert isinstance(new_root, Node)
            assert isinstance(new_pointer, Node)
            self.append_pointer.append_child(new_root)
            self.append_pointer = new_pointer
            return

        self.append_pointer.append_child(node)
        self.append_pointer = node


# -- Node types --


class Node(TreeNode):
    """
    A node in the document tree with builder support.

    Extends TreeNode with the >> operator for building HTML trees,
    and a factory method for creating nodes from various content types.
    """

    __slots__ = ()

    @classmethod
    def factory(cls, contents: NodeContent) -> Node:
        if isinstance(contents, Node):
            return contents
        if isinstance(contents, Fragment):
            root = contents.root
            if root.parent_node is not None:
                return root.clone_node(deep=True)
            return root
        if is_async_content_fn(contents):
            return Async(contents)
        if is_sync_content_fn(contents):
            return Lazy(contents)
        raise ValueError(f"Unsupported type for >>: {type(contents)}")

    def _stream(self, ctx: RenderContext | None = None) -> Generator[str]:
        yield from stream_children(self.children, ctx)

    async def _astream(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        async for chunk in astream_children(self.children, ctx):
            yield chunk

    def render(
        self,
        *,
        args: dict[str, object] | None = None,
        plugins: tuple[Plugin, ...] | None = None,
        max_depth: int = 100,
        max_nodes: int | None = None,
    ) -> str:
        return _render_impl(self, args=args, plugins=plugins, max_depth=max_depth, max_nodes=max_nodes)

    def stream(
        self,
        *,
        args: dict[str, object] | None = None,
        plugins: tuple[Plugin, ...] | None = None,
        max_depth: int = 100,
        max_nodes: int | None = None,
    ) -> Generator[str]:
        return _stream_impl(self, args=args, plugins=plugins, max_depth=max_depth, max_nodes=max_nodes)

    def astream(
        self,
        *,
        args: dict[str, object] | None = None,
        plugins: tuple[Plugin, ...] | None = None,
        min_chunk_size: int | None = 4096,
        cancel_scope: anyio.CancelScope | None = None,
        max_depth: int = 100,
        max_nodes: int | None = None,
    ) -> AsyncGenerator[str]:
        return _astream_impl(
            self,
            args=args,
            plugins=plugins,
            min_chunk_size=min_chunk_size,
            cancel_scope=cancel_scope,
            max_depth=max_depth,
            max_nodes=max_nodes,
        )

    @overload
    def __rshift__(self, other: NodeContent) -> Fragment: ...

    @overload
    def __rshift__(self, other: None) -> None: ...

    @overload
    def __rshift__(self, other: Literal[False]) -> None: ...

    def __rshift__(self, other):
        if other is None or other is False:
            return None

        new_fragment = Fragment(self, self)

        if isinstance(other, str | Template):
            self.children.append(other)
            return new_fragment

        if isinstance(other, tuple | list):
            _flatten_into(self, other)
            return new_fragment

        if isinstance(other, Fragment):
            new_fragment.append(other)
            return new_fragment

        if isinstance(other, Node):
            new_fragment.append(other)
            return new_fragment

        if isinstance(other, Iterable):
            _flatten_into(self, other)
            return new_fragment

        node = Node.factory(other)
        new_fragment.append(node)

        return new_fragment

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


class Comment(Node):
    """An HTML Comment Node."""

    __slots__ = ("content",)

    content: str | Template

    def __init__(self, content: str | Template, /):
        super().__init__()
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

    def _stream(self, ctx: RenderContext | None = None) -> Generator[str]:
        yield f"<!--{self._escape_content()}-->"

    async def _astream(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        yield f"<!--{self._escape_content()}-->"


class Element(Node):
    """An HTML Element with tag, attributes, and builder support."""

    __slots__ = ("attributes", "_style", "_class_list", "_dataset", "_open_tag_cache")

    tag: ClassVar[str]
    void: ClassVar[bool] = False
    doctype: ClassVar[str] = ""
    attributes: dict[str, object]
    _open_tag_cache: str

    def __init__(self, attributes: dict[str, object] | None = None, /, **keyword_attributes: object):
        super().__init__()
        if attributes:
            merged: dict[str, object] = {k.lower(): v for k, v in attributes.items()}
            for k, v in keyword_attributes.items():
                merged[_convert_attribute_names(k)] = v
            self.attributes = merged
        elif keyword_attributes:
            self.attributes = {_convert_attribute_names(k): v for k, v in keyword_attributes.items()}
        else:
            self.attributes = {}
        self._style: StyleMap | None = None
        self._class_list: ClassList | None = None
        self._dataset: DatasetMap | None = None

    def __repr__(self):
        return f"{type(self)}({self.tag!r}, {self.attributes!r})"

    def __replace__(self, /, **changes):
        new_obj = type(self)()
        new_obj.attributes = dict(self.attributes)
        new_children = changes.get("children", self.children)
        if new_children:
            for child in new_children:
                if isinstance(child, TreeNode):
                    new_obj.append_child(copy.replace(child))
                else:
                    new_obj.children.append(child)
        return new_obj

    def __getitem__(self, name: str) -> object:
        return self.attributes[name.lower()]

    def _invalidate_open_tag_cache(self) -> None:
        with suppress(AttributeError):
            del self._open_tag_cache

    def __setitem__(self, name: str, value: object) -> None:
        self.attributes[name.lower()] = value
        self._invalidate_open_tag_cache()

    def __delitem__(self, name: str) -> None:
        del self.attributes[name.lower()]
        self._invalidate_open_tag_cache()

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

    def _stream(self, ctx: RenderContext | None = None) -> Generator[str]:
        tag = self.tag
        attrs = self._render_attrs()
        if self.void:
            yield render_open_tag(tag, attrs, void=True)
        else:
            if self.doctype:
                yield self.doctype
            yield render_open_tag(tag, attrs)
            yield from stream_children(self.children, ctx)
            yield f"</{tag}>"

    async def _astream(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        tag = self.tag
        attrs = self._render_attrs()
        if self.void:
            yield render_open_tag(tag, attrs, void=True)
        else:
            if self.doctype:
                yield self.doctype
            yield render_open_tag(tag, attrs)
            async for chunk in astream_children(self.children, ctx):
                yield chunk
            yield f"</{tag}>"


class VoidElement(Element):
    """An HTML element that cannot have children (e.g., img, br, input)."""

    __slots__ = ()

    void: ClassVar[bool] = True

    def append_child(self, child: object) -> NoReturn:
        raise ValueError(f"Cannot add children to a void element ({self.tag})")

    def __rshift__(self, other: object) -> NoReturn:
        raise ValueError(f"Cannot add children to a void element ({self.tag})")


class Lazy(Node):
    """Wraps a sync callable, resolved during rendering."""

    __slots__ = ("fn", "args", "kwargs")

    _may_block: ClassVar[bool] = True

    fn: Callable[..., NodeContent]
    args: tuple[object, ...]
    kwargs: dict[str, object]

    def __init__(self, fn: Callable[..., NodeContent], /, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def __repr__(self):
        parts = [repr(self.fn)]
        parts.extend(repr(a) for a in self.args)
        parts.extend(f"{k}={v!r}" for k, v in self.kwargs.items())
        return f"Lazy({', '.join(parts)})"

    def __replace__(self, **changes):
        return type(self)(self.fn, *self.args, **self.kwargs)

    def _stream(self, ctx: RenderContext | None = None) -> Generator[str]:
        if ctx is not None:
            if ctx._depth >= ctx.max_depth:
                raise RenderLimitExceeded(f"Exceeded max render depth ({ctx.max_depth})")
            ctx._depth += 1
        yield from render_result(self.fn(*self.args, **self.kwargs), ctx)
        if ctx is not None:
            ctx._depth -= 1

    async def _astream(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        if ctx is not None:
            if ctx._depth >= ctx.max_depth:
                raise RenderLimitExceeded(f"Exceeded max render depth ({ctx.max_depth})")
            ctx._depth += 1
        async for chunk in arender_result(self.fn(*self.args, **self.kwargs), ctx):
            yield chunk
        if ctx is not None:
            ctx._depth -= 1


class Async(Node):
    """Wraps an async callable, resolved during async rendering."""

    __slots__ = ("fn", "args", "kwargs")

    _may_block: ClassVar[bool] = True

    fn: Callable[..., Awaitable[NodeContent]]
    args: tuple[object, ...]
    kwargs: dict[str, object]

    def __init__(self, fn: Callable[..., Awaitable[NodeContent]], /, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def __repr__(self):
        parts = [repr(self.fn)]
        parts.extend(repr(a) for a in self.args)
        parts.extend(f"{k}={v!r}" for k, v in self.kwargs.items())
        return f"Async({', '.join(parts)})"

    def __replace__(self, **changes):
        return type(self)(self.fn, *self.args, **self.kwargs)

    def _stream(self, ctx: RenderContext | None = None) -> Generator[str]:
        raise TypeError("Async nodes require async rendering")

    async def _astream(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        if ctx is not None:
            if ctx._depth >= ctx.max_depth:
                raise RenderLimitExceeded(f"Exceeded max render depth ({ctx.max_depth})")
            ctx._depth += 1
        async for chunk in arender_result(await self.fn(*self.args, **self.kwargs), ctx):
            yield chunk
        if ctx is not None:
            ctx._depth -= 1


class ConditionalNode(Node):
    """Renders content conditionally based on a Var's truthiness."""

    __slots__ = ("var", "if_true", "if_false")

    var: Var
    if_true: NodeContent
    if_false: NodeContent | None

    def __init__(self, var: Var, if_true: NodeContent, if_false: NodeContent | None = None):
        super().__init__()
        self.var = var
        self.if_true = if_true
        self.if_false = if_false

    def __repr__(self) -> str:
        if self.if_false is not None:
            return f"ConditionalNode({self.var!r}, {self.if_true!r}, {self.if_false!r})"
        return f"ConditionalNode({self.var!r}, {self.if_true!r})"

    def __replace__(self, **changes):
        return ConditionalNode(self.var, self.if_true, self.if_false)

    def __or__(self, content: NodeContent, /) -> ConditionalNode:
        if self.if_false is not None:
            raise TypeError("ConditionalNode already has an else branch")
        return ConditionalNode(self.var, self.if_true, if_false=content)

    def __rshift__(self, other: object) -> NoReturn:
        raise TypeError("ConditionalNode does not support >> \u2014 content is set via & and |")

    def append_child(self, child: object) -> NoReturn:
        raise TypeError("ConditionalNode does not support children")

    def _stream(self, ctx: RenderContext | None = None) -> Generator[str]:
        val = self.var()
        branch = self.if_true if val else self.if_false
        if branch is None:
            return
        yield from render_result(branch, ctx)

    async def _astream(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        val = self.var()
        branch = self.if_true if val else self.if_false
        if branch is None:
            return
        async for chunk in arender_result(branch, ctx):
            yield chunk


class IterationNode(Node):
    """Renders content for each item in a Var's iterable value."""

    __slots__ = ("var", "body_fn")

    var: Var
    body_fn: Callable[[Any], NodeContent]

    def __init__(self, var: Var, body_fn: Callable[[Any], NodeContent]):
        super().__init__()
        self.var = var
        self.body_fn = body_fn

    def __repr__(self) -> str:
        return f"IterationNode({self.var!r}, {self.body_fn!r})"

    def __replace__(self, **changes):
        return IterationNode(self.var, self.body_fn)

    def __rshift__(self, other: object) -> NoReturn:
        raise TypeError("IterationNode does not support >> \u2014 content is set via .map()")

    def append_child(self, child: object) -> NoReturn:
        raise TypeError("IterationNode does not support children")

    def _stream(self, ctx: RenderContext | None = None) -> Generator[str]:
        items = self.var()
        for item in items:
            yield from render_result(self.body_fn(item), ctx)

    async def _astream(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        items = self.var()
        for item in items:
            async for chunk in arender_result(self.body_fn(item), ctx):
                yield chunk


_MISSING = object()


class Var:
    """A named variable for use in preserved trees.

    Callable — works in t-string interpolations (evaluated at render time)
    and auto-wraps as Lazy when used as a child node via >>.

    Values are passed via render()/stream()/astream() ``vars`` parameter.
    """

    __slots__ = ("name", "default")

    def __init__(self, name: str, *, default: object = _MISSING):
        self.name = name
        self.default = default

    def __call__(self) -> Any:
        vars = _render_vars.get()
        if vars and self.name in vars:
            return vars[self.name]
        if self.default is not _MISSING:
            return self.default
        raise LookupError(f"Var {self.name!r} not set")

    def __repr__(self) -> str:
        return f"Var({self.name!r})"

    def __and__(self, content: NodeContent, /) -> ConditionalNode:
        return ConditionalNode(self, content)

    def map(self, fn: Callable[[Any], NodeContent], /) -> IterationNode:
        return IterationNode(self, fn)


class _VarNamespace:
    """Attribute-access shorthand for creating Var instances: ``args.title`` → ``Var("title")``."""

    __slots__ = ()

    def __getattr__(self, name: str) -> Var:
        return Var(name)

    def __repr__(self) -> str:
        return "args"


args = _VarNamespace()
