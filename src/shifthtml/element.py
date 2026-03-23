from __future__ import annotations

import copy
import inspect
from collections.abc import AsyncGenerator, Awaitable, Callable, Generator, Iterable, Iterator, Sequence
from string.templatelib import Template
from typing import Any, ClassVar, NoReturn, overload

import anyio

from .mappings import ClassList, DatasetMap, StyleMap, _snake_to_kebab
from .plugin import Plugin, RenderContext
from .render import arender_string, render_open_tag, render_string, render_string_to_list
from .tree import TreeNode
from .types import NodeContent, NodeListContent


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


async def _arender_children(children: list[TreeNode], ctx: RenderContext | None = None) -> AsyncGenerator[str]:
    if len(children) <= 1:
        for child in children:
            if ctx is not None:
                async for chunk in ctx.arender_node(child):
                    yield chunk
            else:
                async for chunk in child.arender():
                    yield chunk
        return

    results: list[list[str]] = [[] for _ in children]
    ready: list[anyio.Event] = [anyio.Event() for _ in children]

    async def collect(i: int, child: TreeNode) -> None:
        if ctx is not None:
            results[i] = [chunk async for chunk in ctx.arender_node(child)]
        else:
            results[i] = [chunk async for chunk in child.arender()]
        ready[i].set()

    async with anyio.create_task_group() as tg:
        for i, child in enumerate(children):
            tg.start_soon(collect, i, child)

        for i in range(len(children)):
            await ready[i].wait()
            for chunk in results[i]:
                yield chunk


class Fragment:
    """
    A document fragment that can contain nodes and other fragments.
    Not a DOM node — a builder wrapper around a DOM tree.
    """

    __slots__ = ("root", "append_pointer", "plugins")

    root: TreeNode
    append_pointer: TreeNode

    def __init__(self, root: TreeNode, append_pointer: TreeNode, /):
        self.root = root
        self.append_pointer = append_pointer
        self.plugins: tuple[Plugin, ...] = ()

    def __copy__(self) -> Fragment:
        frag = Fragment(self.root, self.append_pointer)
        frag.plugins = self.plugins
        return frag

    def __deepcopy__(self, memo=None) -> Fragment:
        new_root, new_pointer = _copy_tree(self.root, self.append_pointer)
        if new_pointer is None:
            raise ValueError("Pointer target not found in the tree")
        frag = Fragment(new_root, new_pointer)
        frag.plugins = self.plugins
        return frag

    def __replace__(self, /, **changes):
        return copy.deepcopy(self)

    def __repr__(self):
        return f"Fragment({self.root!r}, {self.append_pointer!r})"

    def __str__(self):
        if self.plugins:
            return "".join(self.render())
        buf: list[str] = []
        self.root.render_to_buf(buf)
        return "".join(buf)

    def __iter__(self) -> Iterator[TreeNode]:
        return iter(self.root.children)

    @overload
    def __rshift__(self, other: None) -> None: ...

    @overload
    def __rshift__(self, other: NodeContent) -> Fragment: ...

    def __rshift__(self, other):
        if other is None:
            return None

        new_fragment = copy.deepcopy(self)

        if isinstance(other, Fragment):
            new_fragment.append(copy.deepcopy(other))
            return new_fragment

        node = Node.factory(other)
        new_fragment.append(node)

        return new_fragment

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

    def render(self) -> Generator[str]:
        if self.plugins:
            ctx = RenderContext(plugins=self.plugins)
            yield from ctx.pre_render_all()
            yield from self._render_root(ctx)
        else:
            yield from self.root.render()

    def _render_root(self, ctx: RenderContext) -> Generator[str]:
        root = self.root
        for plugin in ctx.plugins:
            result = plugin.pre_render_node(root, ctx)
            if result is not None:
                yield from result
                yield from ctx._post_render_node(root)
                yield from ctx.post_render_all()
                return

        if isinstance(root, Element) and not root.void:
            yield from root.render(ctx=ctx, before_close=ctx.post_render_all)
        else:
            yield from root.render(ctx=ctx)
            yield from ctx.post_render_all()
        yield from ctx._post_render_node(root)

    async def arender(
        self, *, min_chunk_size: int | None = 4096, cancel_scope: anyio.CancelScope | None = None
    ) -> AsyncGenerator[str]:
        if min_chunk_size is None:
            async for chunk in self._arender_unbuffered(cancel_scope=cancel_scope):
                yield chunk
            return

        buf: list[str] = []
        buf_size = 0
        async for chunk in self._arender_unbuffered(cancel_scope=cancel_scope):
            buf.append(chunk)
            buf_size += len(chunk)
            if buf_size >= min_chunk_size:
                yield "".join(buf)
                buf.clear()
                buf_size = 0
        if buf:
            yield "".join(buf)

    async def _arender_unbuffered(self, *, cancel_scope: anyio.CancelScope | None = None) -> AsyncGenerator[str]:
        if self.plugins:
            ctx = RenderContext(plugins=self.plugins, cancel_scope=cancel_scope)
            async for chunk in ctx.apre_render_all():
                yield chunk
            async for chunk in self._arender_root(ctx):
                yield chunk
        else:
            async for chunk in self.root.arender():
                yield chunk

    async def _arender_root(self, ctx: RenderContext) -> AsyncGenerator[str]:
        root = self.root
        for plugin in ctx.plugins:
            ahook = getattr(plugin, "apre_render_node", None)
            result = ahook(root, ctx) if ahook is not None else plugin.pre_render_node(root, ctx)
            if result is not None:
                if isinstance(result, AsyncGenerator):
                    async for chunk in result:
                        yield chunk
                else:
                    for chunk in result:
                        yield chunk
                async for chunk in ctx._apost_render_node(root):
                    yield chunk
                async for chunk in ctx.apost_render_all():
                    yield chunk
                return

        if isinstance(root, Element) and not root.void:
            async for chunk in root.arender(ctx=ctx, before_close=ctx.apost_render_all):
                yield chunk
        else:
            async for chunk in root.arender(ctx=ctx):
                yield chunk
            async for chunk in ctx.apost_render_all():
                yield chunk
        async for chunk in ctx._apost_render_node(root):
            yield chunk


class Node(TreeNode):
    """
    A node in the document tree with builder support.

    Extends the abstract Node with the >> operator for building HTML trees,
    and a factory method for creating nodes from various content types.
    """

    __slots__ = ()

    @classmethod
    def factory(cls, contents: NodeContent) -> Node:
        if isinstance(contents, Node):
            return contents
        if isinstance(contents, Fragment):
            return NodeList([contents])
        if isinstance(contents, str | Template):
            return Text(contents)
        if isinstance(contents, type) and issubclass(contents, TreeNode):
            return contents()  # type: ignore[return-value]  # tag classes always produce Node subclasses
        if callable(contents):
            if inspect.iscoroutinefunction(contents):
                return Async(contents)
            return Lazy(contents)  # type: ignore[arg-type]  # ty can't narrow callable after isinstance/iscoroutinefunction checks
        if isinstance(contents, Iterable):
            return NodeList(contents)
        raise ValueError(f"Unsupported shift type for >>: {type(contents)}")

    @overload
    def __rshift__(self, other: NodeContent) -> Fragment: ...

    @overload
    def __rshift__(self, other: None) -> None: ...

    def __rshift__(self, other):
        if other is None:
            return None

        new_fragment = Fragment(self, self)

        if isinstance(other, Fragment):
            new_fragment.append(other)
            return new_fragment

        node = Node.factory(other)
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
        buf: list[str] = []
        self.render_to_buf(buf)
        return "".join(buf)

    def render_to_buf(self, buf: list[str]) -> None:
        for child in self.children:
            child.render_to_buf(buf)

    def render(self, *, ctx: RenderContext | None = None) -> Generator[str]:
        for child in self.children:
            if ctx is not None:
                yield from ctx.render_node(child)
            else:
                yield from child.render()

    async def arender(self, *, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        async for chunk in _arender_children(self.children, ctx):
            yield chunk


class NodeList(Node, Sequence[TreeNode]):
    """A list of nodes with a position in the tree."""

    __slots__ = ()

    def __init__(self, contents: NodeListContent, /):
        super().__init__()

        for item in contents:
            if item is None:
                continue

            if isinstance(item, Fragment):
                self.append_child(item.root)
            else:
                node = Node.factory(item)
                self.append_child(node)

    def __replace__(self, /, **changes):
        new_obj = NodeList([])
        new_children = changes.get("children", self.children)
        if new_children:
            for child in new_children:
                new_obj.append_child(copy.replace(child))
        return new_obj

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

    __slots__ = ("content",)

    content: str | Template

    def __init__(self, content: str | Template, /):
        super().__init__()
        self.content = content

    def __repr__(self):
        return f"Text({self.content!r})"

    def __replace__(self, **changes):
        return type(self)(self.content)

    def append_child(self, child):
        raise ValueError("Cannot add children to a Text node")

    def render_to_buf(self, buf: list[str]) -> None:
        render_string_to_list(self.content, buf)

    def render(self, *, ctx: RenderContext | None = None) -> Generator[str]:
        yield from render_string(self.content)

    async def arender(self, *, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        async for chunk in arender_string(self.content):
            yield chunk


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

    def render_to_buf(self, buf: list[str]) -> None:
        buf.append(f"<!--{self._escape_content()}-->")

    def render(self, *, ctx: RenderContext | None = None) -> Generator[str]:
        yield f"<!--{self._escape_content()}-->"

    async def arender(self, *, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        yield f"<!--{self._escape_content()}-->"


class Element(Node):
    """An HTML Element with tag, attributes, and builder support."""

    __slots__ = ("attributes", "_style", "_class_list", "_dataset")

    tag: ClassVar[str]
    void: ClassVar[bool] = False
    attributes: dict[str, str | Template]

    def __init__(self, attributes: dict[str, str | Template] | None = None, /, **keyword_attributes: str | Template):
        super().__init__()
        merged: dict[str, str | Template] = {k.lower(): v for k, v in attributes.items()} if attributes else {}
        merged.update({_convert_attribute_names(key): value for key, value in keyword_attributes.items()})
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
        return self.tag

    def __getitem__(self, name: str) -> str | Template:
        return self.attributes[name.lower()]

    def __setitem__(self, name: str, value: str | Template) -> None:
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

    def _render_attrs(self) -> dict[str, str | Template]:
        if self._style:
            return {**self.attributes, "style": self._style.css_text}
        return self.attributes

    def render_to_buf(self, buf: list[str]) -> None:
        attrs = self._render_attrs()
        if self.void:
            buf.append(render_open_tag(self.tag, attrs, void=True))
        else:
            buf.append(render_open_tag(self.tag, attrs))
            for child in self.children:
                child.render_to_buf(buf)
            buf.append(f"</{self.tag}>")

    def render(
        self,
        *,
        ctx: RenderContext | None = None,
        before_close: Callable[[], Generator[str]] | None = None,
    ) -> Generator[str]:
        attrs = self._render_attrs()
        if self.void:
            yield render_open_tag(self.tag, attrs, void=True)
        else:
            yield render_open_tag(self.tag, attrs)
            for child in self.children:
                if ctx is not None:
                    yield from ctx.render_node(child)
                else:
                    yield from child.render()
            if before_close is not None:
                yield from before_close()
            yield f"</{self.tag}>"

    async def arender(
        self,
        *,
        ctx: RenderContext | None = None,
        before_close: Callable[[], AsyncGenerator[str]] | None = None,
    ) -> AsyncGenerator[str]:
        attrs = self._render_attrs()
        if self.void:
            yield render_open_tag(self.tag, attrs, void=True)
        else:
            yield render_open_tag(self.tag, attrs)
            async for chunk in _arender_children(self.children, ctx):
                yield chunk
            if before_close is not None:
                async for chunk in before_close():
                    yield chunk
            yield f"</{self.tag}>"


class VoidElement(Element):
    """An HTML element that cannot have children (e.g., img, br, input)."""

    __slots__ = ()

    void: ClassVar[bool] = True

    def append_child(self, child: object) -> NoReturn:
        raise ValueError(f"Cannot add children to a void element ({self.tag})")

    def __rshift__(self, other: object) -> NoReturn:
        raise ValueError(f"Cannot add children to a void element ({self.tag})")


class Deferred(Node):
    __slots__ = ("loading_node", "slot_name")

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
        return type(self)(copy.replace(self.children[0]), slot_name=self.slot_name, loading=self.loading_node)

    def render(self, *, ctx: RenderContext | None = None) -> Generator[str]:
        raise TypeError("Deferred nodes require DeferPlugin")

    async def arender(self, *, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        raise TypeError("Deferred nodes require DeferPlugin")
        yield  # pragma: no cover


class Lazy(Node):
    """Wraps a sync callable, resolved during rendering."""

    __slots__ = ("fn",)

    fn: Callable[[], NodeContent]

    def __init__(self, fn: Callable[[], NodeContent], /):
        super().__init__()
        self.fn = fn

    def __repr__(self):
        return f"Lazy({self.fn!r})"

    def __replace__(self, **changes):
        return type(self)(self.fn)

    def render_to_buf(self, buf: list[str]) -> None:
        result = self.fn()
        if result is None:
            return
        node = Node.factory(result)
        node.render_to_buf(buf)

    def render(self, *, ctx: RenderContext | None = None) -> Generator[str]:
        result = self.fn()
        if result is None:
            return
        node = Node.factory(result)
        if ctx is not None:
            yield from ctx.render_node(node)
        else:
            yield from node.render()

    async def arender(self, *, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        result = self.fn()
        if result is None:
            return
        node = Node.factory(result)
        if ctx is not None:
            async for chunk in ctx.arender_node(node):
                yield chunk
        else:
            async for chunk in node.arender():
                yield chunk


class Async(Node):
    """Wraps an async callable, resolved during async rendering."""

    __slots__ = ("fn",)

    fn: Callable[[], Awaitable[NodeContent]]

    def __init__(self, fn: Callable[[], Awaitable[NodeContent]], /):
        super().__init__()
        self.fn = fn

    def __repr__(self):
        return f"Async({self.fn!r})"

    def __replace__(self, **changes):
        return type(self)(self.fn)

    def render(self, *, ctx: RenderContext | None = None) -> Generator[str]:
        raise TypeError("Async nodes require async rendering")

    async def arender(self, *, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        result = await self.fn()
        node = Node.factory(result)
        if ctx is not None:
            async for chunk in ctx.arender_node(node):
                yield chunk
        else:
            async for chunk in node.arender():
                yield chunk
