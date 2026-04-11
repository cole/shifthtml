from __future__ import annotations

import copy
from collections.abc import AsyncGenerator, Awaitable, Callable, Generator, Iterable, Iterator
from html import escape as _escape
from string.templatelib import Interpolation, Template
from typing import Any, ClassVar, Literal, NoReturn, overload

import anyio

from .errors import RenderLimitExceeded
from .mappings import ClassList, DatasetMap, StyleMap, _snake_to_kebab
from .rendering import (
    RenderContext,
    _arender_node,
    _collect_children,
    _collect_result,
    _render_node,
    aflush_deferred,
    arender_result,
    astream_children,
    collect_string,
    flush_deferred,
    render_open_tag,
    render_result,
    stream_children,
)
from .tree import Node, _render_vars
from .types import _MISSING, NodeContent, is_async_content_fn, is_sync_content_fn

_FLATTEN_MAX_DEPTH = 100
_EMPTY_ARGS: dict[str, object] = {}


def _wrap_content(contents: NodeContent) -> Node:
    """Wrap remaining NodeContent types (Node, Fragment, callables) into a tree node."""
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
    raise ValueError(f"Unsupported type: {type(contents)}")


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
        if item is None or item is False:
            continue
        item_type = type(item)
        if item_type is Fragment:
            item = item.root
            if item.parent_node is not None:
                item = item.clone_node(deep=True)
            item.parent_node = parent
            children.append(item)
        elif item_type is str or isinstance(item, Template):
            children.append(item)
        elif isinstance(item, Node):
            if item.parent_node is not None:
                item = item.clone_node(deep=True)
            item.parent_node = parent
            children.append(item)
        elif isinstance(item, Iterable):
            _flatten_into(parent, item, _depth=_depth + 1)
        else:
            node = _wrap_content(item)
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


# -- Render cache helpers --


def _is_static_template(template: Template) -> bool:
    return not any(callable(item.value) for item in template if isinstance(item, Interpolation))


_UNCACHEABLE: list = []


def _build_render_buf(node: Node, buf: list) -> bool:
    """Walk a tree and build a reusable render buffer.

    Static content is pre-rendered as strings. Dynamic content (Var-bound
    Templates, Lazy/Async nodes) is stored as refs resolved at each render.

    Returns False if the tree contains Deferred nodes (render cache unusable).
    """
    if isinstance(node, Element):
        if node.doctype:
            buf.append(node.doctype)
        buf.append(render_open_tag(node.tag, node._render_attrs(), void=node.void))
        if not node.void:
            if not _build_children(node.children, buf):
                return False
            buf.append(f"</{node.tag}>")
    elif getattr(node, "_deferred_node", False):
        return False
    elif isinstance(node, IterationNode):
        buf.append(node)
    elif isinstance(node, Lazy | Async | ConditionalNode):
        buf.append(node)  # Dynamic — resolved at render time
    elif isinstance(node, Comment):
        buf.append(f"<!--{node._escape_content()}-->")
    elif isinstance(node, ContentNode):
        if not _build_children(node.children, buf):
            return False
    else:
        buf.append(node)
    return True


def _build_children(children: list, buf: list) -> bool:
    for child in children:
        if type(child) is str:
            buf.append(_escape(child) if ("&" in child or "<" in child or ">" in child) else child)
        elif isinstance(child, Node):
            if not _build_render_buf(child, buf):
                return False
        elif isinstance(child, Template):
            if _is_static_template(child):
                collect_string(child, buf)
            else:
                buf.append(child)
    return True


def _compact_render_buf(buf: list) -> list:
    """Merge adjacent strings in a render buffer."""
    result: list = []
    pending: list[str] = []
    for item in buf:
        if type(item) is str:
            pending.append(item)
        else:
            if pending:
                result.append("".join(pending) if len(pending) > 1 else pending[0])
                pending.clear()
            result.append(item)
    if pending:
        result.append("".join(pending) if len(pending) > 1 else pending[0])
    return result


def _resolve_render_buf(buf: list, out: list[str]) -> None:
    """Resolve a render buffer into output strings."""
    for item in buf:
        if type(item) is str:
            out.append(item)
        elif isinstance(item, Template):
            collect_string(item, out)
        else:  # Node — has _collect
            item._collect(out)


# -- Fragment --


class Fragment:
    """A document fragment — a builder wrapper around a DOM tree."""

    __slots__ = ("root", "append_pointer", "_render_cache")

    root: Node
    append_pointer: Node
    _render_cache: list | None

    def __init__(self, root: Node, append_pointer: Node, /):
        self.root = root
        self.append_pointer = append_pointer
        self._render_cache = None

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

    def render(
        self,
        *,
        args: dict[str, object] | None = None,
        max_depth: int = 100,
        max_nodes: int | None = None,
    ) -> str:
        # Fast path: use reusable render buffer (no limits, no deferred nodes)
        if max_nodes is None and max_depth == 100 and isinstance(self.root, ContentNode):
            _render_vars.set(args if args is not None else _EMPTY_ARGS)
            render_cache = self._render_cache
            if render_cache is None:
                raw: list = []
                cacheable = _build_render_buf(self.root, raw)
                if cacheable:
                    render_cache = _compact_render_buf(raw)
                    self._render_cache = render_cache
                else:
                    self._render_cache = _UNCACHEABLE
            if render_cache is not None and render_cache is not _UNCACHEABLE:
                out: list[str] = []
                _resolve_render_buf(render_cache, out)
                return "".join(out)
        if isinstance(self.root, ContentNode):
            return self.root.render(args=args, max_depth=max_depth, max_nodes=max_nodes)
        return self.root.render(args=args)

    def stream(
        self,
        *,
        args: dict[str, object] | None = None,
        max_depth: int = 100,
        max_nodes: int | None = None,
    ) -> Generator[str]:
        if isinstance(self.root, ContentNode):
            return self.root.stream(args=args, max_depth=max_depth, max_nodes=max_nodes)
        return self.root.stream(args=args)

    def astream(
        self,
        *,
        args: dict[str, object] | None = None,
        min_chunk_size: int | None = 4096,
        cancel_scope: anyio.CancelScope | None = None,
        max_depth: int = 100,
        max_nodes: int | None = None,
    ) -> AsyncGenerator[str]:
        if isinstance(self.root, ContentNode):
            return self.root.astream(
                args=args,
                min_chunk_size=min_chunk_size,
                cancel_scope=cancel_scope,
                max_depth=max_depth,
                max_nodes=max_nodes,
            )
        return self.root.astream(args=args)

    def _stream(self, ctx: RenderContext | None = None) -> Generator[str]:
        if ctx is not None:
            yield from _render_node(self.root, ctx)
        else:
            yield from self.root._stream()

    async def _astream(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        if ctx is not None:
            async for chunk in _arender_node(self.root, ctx):
                yield chunk
        else:
            async for chunk in self.root._astream():
                yield chunk

    def _collect(self, buf: list[str]) -> None:
        self.root._collect(buf)

    def __str__(self) -> str:
        root = self.root
        if isinstance(root, ContentNode):
            result_buf: list[str] = []
            root._collect(result_buf)
            return "".join(result_buf)
        return self.render()

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

        self._render_cache = None
        other_type = type(other)

        if other_type is str:
            self.append_pointer.children.append(other)
            return self

        if isinstance(other, Template):
            self.append_pointer.children.append(other)
            return self

        if other_type is tuple or other_type is list:
            _flatten_into(self.append_pointer, other)
            return self

        if other_type is Fragment:
            self.append(other)
            return self

        if isinstance(other, Node):
            self.append(other)
            return self

        if isinstance(other, Iterable):
            _flatten_into(self.append_pointer, other)
            return self

        node = _wrap_content(other)
        self.append(node)
        return self

    def append(self, node: Node | Fragment) -> None:
        """Modify the tree by appending a node to the end."""
        self._render_cache = None
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


# -- ContentNode types --


class ContentNode(Node):
    """
    A node in the document tree with builder support.

    Extends Node with the >> operator for building HTML trees,
    and a factory method for creating nodes from various content types.
    """

    __slots__ = ()

    def _collect(self, buf: list[str]) -> None:
        """Collect rendered HTML into a buffer (non-generator fast path)."""
        _collect_children(self.children, buf)

    def _stream(self, ctx: RenderContext | None = None) -> Generator[str]:
        yield from stream_children(self.children, ctx)

    async def _astream(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        async for chunk in astream_children(self.children, ctx):
            yield chunk

    def render(
        self,
        *,
        args: dict[str, object] | None = None,
        max_depth: int = 100,
        max_nodes: int | None = None,
    ) -> str:
        _render_vars.set(args if args is not None else _EMPTY_ARGS)
        ctx = RenderContext(max_depth=max_depth, max_nodes=max_nodes, _root_node=self)
        parts = list(self._stream(ctx))
        parts.extend(flush_deferred(ctx))
        return "".join(parts)

    def stream(
        self,
        *,
        args: dict[str, object] | None = None,
        max_depth: int = 100,
        max_nodes: int | None = None,
    ) -> Generator[str]:
        _render_vars.set(args or {})
        ctx = RenderContext(max_depth=max_depth, max_nodes=max_nodes, _root_node=self)
        yield from self._stream(ctx)
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
        _render_vars.set(args or {})
        if min_chunk_size is None:
            async for chunk in self._astream_unbuffered(
                cancel_scope=cancel_scope, max_depth=max_depth, max_nodes=max_nodes
            ):
                yield chunk
            return

        buf: list[str] = []
        buf_size = 0
        async for chunk in self._astream_unbuffered(
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

    async def _astream_unbuffered(
        self,
        *,
        cancel_scope: anyio.CancelScope | None = None,
        max_depth: int = 100,
        max_nodes: int | None = None,
    ) -> AsyncGenerator[str]:
        ctx = RenderContext(cancel_scope=cancel_scope, max_depth=max_depth, max_nodes=max_nodes, _root_node=self)
        async for chunk in self._astream(ctx):
            yield chunk
        async for chunk in aflush_deferred(ctx):
            yield chunk

    @overload
    def __rshift__(self, other: NodeContent) -> Fragment: ...

    @overload
    def __rshift__(self, other: None) -> None: ...

    @overload
    def __rshift__(self, other: Literal[False]) -> None: ...

    def __rshift__(self, other):
        if other is None or other is False:
            return None
        return Fragment(self, self).__rshift__(other)

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


class Comment(ContentNode):
    """An HTML Comment ContentNode."""

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

    def _collect(self, buf: list[str]) -> None:
        buf.append(f"<!--{self._escape_content()}-->")

    def _stream(self, ctx: RenderContext | None = None) -> Generator[str]:
        yield f"<!--{self._escape_content()}-->"

    async def _astream(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        yield f"<!--{self._escape_content()}-->"


class Element(ContentNode):
    """An HTML Element with tag, attributes, and builder support."""

    __slots__ = ("attributes", "_style", "_class_list", "_dataset")

    tag: ClassVar[str]
    _close_tag: ClassVar[str] = ""
    _bare_open: ClassVar[str] = ""
    _tag_prefix: ClassVar[str] = ""
    _class_prefix: ClassVar[str] = ""
    void: ClassVar[bool] = False
    doctype: ClassVar[str] = ""
    attributes: dict[str, object]

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "tag"):
            cls._close_tag = f"</{cls.tag}>"
            cls._bare_open = f"<{cls.tag}>"
            cls._tag_prefix = f"<{cls.tag} "
            cls._class_prefix = f'<{cls.tag} class="'

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

    def _collect(self, buf: list[str]) -> None:
        # Inline open tag for 0-1 string attrs (99% of elements)
        attrs = {**self.attributes, "style": self._style.css_text} if self._style else self.attributes
        if attrs:
            if len(attrs) == 1:
                (key,) = attrs
                value = attrs[key]
                if type(value) is str:
                    if "&" in value or "<" in value or ">" in value or '"' in value or "'" in value:
                        value = _escape(value, quote=True)
                    if key == "class":
                        buf.append(f'{self._class_prefix}{value}">')
                    else:
                        buf.append(f'{self._tag_prefix}{key}="{value}">')
                else:
                    buf.append(render_open_tag(self.tag, attrs))
            else:
                buf.append(render_open_tag(self.tag, attrs))
        else:
            buf.append(self._bare_open)
        children = self.children
        n_children = len(children)
        if n_children == 1:
            first = children[0]
            if type(first) is str:
                if "&" in first or "<" in first or ">" in first:
                    buf.append(_escape(first))
                else:
                    buf.append(first)
            elif isinstance(first, Template):
                collect_string(first, buf)
            elif isinstance(first, Node):
                first._collect(buf)
        elif n_children > 1:
            _collect_children(children, buf)
        buf.append(self._close_tag)

    def _stream(self, ctx: RenderContext | None = None) -> Generator[str]:
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

    async def _astream(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
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

    def _collect(self, buf: list[str]) -> None:
        tag = self.tag
        attrs = {**self.attributes, "style": self._style.css_text} if self._style else self.attributes
        if not attrs:
            buf.append(f"<{tag} />")
        elif len(attrs) == 1:
            (key,) = attrs
            value = attrs[key]
            if type(value) is str:
                if "&" in value or "<" in value or ">" in value or '"' in value or "'" in value:
                    value = _escape(value, quote=True)
                buf.append(f'<{tag} {key}="{value}" />')
            else:
                buf.append(render_open_tag(tag, attrs, void=True))
        else:
            buf.append(render_open_tag(tag, attrs, void=True))


class Lazy(ContentNode):
    """Wraps a sync callable, resolved during rendering."""

    __slots__ = ("fn", "args", "kwargs")

    _may_block: ClassVar[bool] = True

    fn: Callable[..., NodeContent]
    args: tuple[object, ...]
    kwargs: dict[str, object]

    def __init__(self, fn: Callable[..., NodeContent], /, *args, **kwargs):
        self.parent_node = None
        self.children = []
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

    def _collect(self, buf: list[str]) -> None:
        _collect_result(self.fn(*self.args, **self.kwargs), buf)

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


class Async(ContentNode):
    """Wraps an async callable, resolved during async rendering."""

    __slots__ = ("fn", "args", "kwargs")

    _may_block: ClassVar[bool] = True

    fn: Callable[..., Awaitable[NodeContent]]
    args: tuple[object, ...]
    kwargs: dict[str, object]

    def __init__(self, fn: Callable[..., Awaitable[NodeContent]], /, *args, **kwargs):
        self.parent_node = None
        self.children = []
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

    def _collect(self, buf: list[str]) -> None:
        raise TypeError("Async nodes require async rendering")

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


class ConditionalNode(ContentNode):
    """Renders content conditionally based on a Var's truthiness."""

    __slots__ = ("var", "if_true", "if_false")

    var: Var
    if_true: NodeContent
    if_false: NodeContent | None

    def __init__(self, var: Var, if_true: NodeContent, if_false: NodeContent | None = None):
        self.parent_node = None
        self.children = []
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

    def _collect(self, buf: list[str]) -> None:
        val = self.var()
        branch = self.if_true if val else self.if_false
        if branch is None:
            return
        _collect_result(branch, buf)

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


class IterationNode(ContentNode):
    """Renders content for each item in a Var's iterable value."""

    __slots__ = ("var", "body_fn")

    var: Var
    body_fn: Callable[[Any], NodeContent]

    def __init__(self, var: Var, body_fn: Callable[[Any], NodeContent]):
        self.parent_node = None
        self.children = []
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

    def _collect(self, buf: list[str]) -> None:
        items = self.var()
        for item in items:
            _collect_result(self.body_fn(item), buf)

    def _stream(self, ctx: RenderContext | None = None) -> Generator[str]:
        items = self.var()
        for item in items:
            yield from render_result(self.body_fn(item), ctx)

    async def _astream(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        items = self.var()
        for item in items:
            async for chunk in arender_result(self.body_fn(item), ctx):
                yield chunk


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
