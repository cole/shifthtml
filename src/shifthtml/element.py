from __future__ import annotations

import copy
from collections.abc import AsyncGenerator, Awaitable, Callable, Generator, Iterable, Iterator
from string.templatelib import Template
from typing import Any, ClassVar, Literal, NoReturn, overload

import anyio

from . import tree as _tree_module
from .errors import RenderLimitExceeded
from .mappings import ClassList, DatasetMap, StyleMap, _snake_to_kebab
from .rendering import (
    RenderContext,
    aflush_deferred,
    arender_result,
    astream_children,
    flush_deferred,
    render_open_tag,
    render_result,
    stream_children,
)
from .tree import Node, _render_vars
from .types import _MISSING, NodeContent, is_async_content_fn, is_sync_content_fn

_FLATTEN_MAX_DEPTH = 100


def normalize(content: NodeContent) -> Node | str | Template | None:
    """Normalize any NodeContent value into a leaf type for tree insertion.

    Returns None for suppressed values (None, False).
    Strings and Templates pass through unchanged.
    Fragments are unwrapped to their root (cloned if already parented).
    Callables are wrapped as Lazy or Async nodes.
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
    if is_async_content_fn(content):
        return Async(content)
    if is_sync_content_fn(content):
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

    def render(
        self,
        *,
        args: dict[str, object] | None = None,
        max_depth: int = 100,
        max_nodes: int | None = None,
    ) -> str:
        return self.root.render(args=args, max_depth=max_depth, max_nodes=max_nodes)

    def stream(
        self,
        *,
        args: dict[str, object] | None = None,
        max_depth: int = 100,
        max_nodes: int | None = None,
    ) -> Generator[str]:
        return self.root.stream(args=args, max_depth=max_depth, max_nodes=max_nodes)

    def astream(
        self,
        *,
        args: dict[str, object] | None = None,
        min_chunk_size: int | None = 4096,
        cancel_scope: anyio.CancelScope | None = None,
        max_depth: int = 100,
        max_nodes: int | None = None,
    ) -> AsyncGenerator[str]:
        return self.root.astream(
            args=args,
            min_chunk_size=min_chunk_size,
            cancel_scope=cancel_scope,
            max_depth=max_depth,
            max_nodes=max_nodes,
        )

    def _chunks(self, ctx: RenderContext | None = None) -> Generator[str]:
        yield from self.root._chunks(ctx)

    async def _achunks(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        async for chunk in self.root._achunks(ctx):
            yield chunk

    def _collect(self, buf: list[str]) -> None:
        self.root._collect(buf)

    def __str__(self) -> str:
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


class Lazy(Node):
    """Wraps a zero-arg sync callable, resolved during rendering."""

    __slots__ = ("fn",)

    _may_block: ClassVar[bool] = True

    fn: Callable[[], NodeContent]

    def __init__(self, fn: Callable[[], NodeContent], /):
        self.parent_node = None
        self.children = []
        self.fn = fn

    def __repr__(self):
        return f"Lazy({self.fn!r})"

    def __replace__(self, **changes):
        return type(self)(self.fn)

    def _chunks(self, ctx: RenderContext | None = None) -> Generator[str]:
        if ctx is not None:
            if ctx._depth >= ctx.max_depth:
                raise RenderLimitExceeded(f"Exceeded max render depth ({ctx.max_depth})")
            ctx._depth += 1
        yield from render_result(self.fn(), ctx)
        if ctx is not None:
            ctx._depth -= 1

    async def _achunks(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        if ctx is not None:
            if ctx._depth >= ctx.max_depth:
                raise RenderLimitExceeded(f"Exceeded max render depth ({ctx.max_depth})")
            ctx._depth += 1
        async for chunk in arender_result(self.fn(), ctx):
            yield chunk
        if ctx is not None:
            ctx._depth -= 1


class Async(Node):
    """Wraps a zero-arg async callable, resolved during async rendering."""

    __slots__ = ("fn",)

    _may_block: ClassVar[bool] = True

    fn: Callable[[], Awaitable[NodeContent]]

    def __init__(self, fn: Callable[[], Awaitable[NodeContent]], /):
        self.parent_node = None
        self.children = []
        self.fn = fn

    def __repr__(self):
        return f"Async({self.fn!r})"

    def __replace__(self, **changes):
        return type(self)(self.fn)

    def _chunks(self, ctx: RenderContext | None = None) -> Generator[str]:
        raise TypeError("Async nodes require async rendering")

    async def _achunks(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        if ctx is not None:
            if ctx._depth >= ctx.max_depth:
                raise RenderLimitExceeded(f"Exceeded max render depth ({ctx.max_depth})")
            ctx._depth += 1
        async for chunk in arender_result(await self.fn(), ctx):
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

    def _chunks(self, ctx: RenderContext | None = None) -> Generator[str]:
        val = self.var()
        branch = self.if_true if val else self.if_false
        if branch is None:
            return
        yield from render_result(branch, ctx)

    async def _achunks(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
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

    def _chunks(self, ctx: RenderContext | None = None) -> Generator[str]:
        items = self.var()
        for item in items:
            yield from render_result(self.body_fn(item), ctx)

    async def _achunks(self, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
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
