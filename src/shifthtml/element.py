from __future__ import annotations

import copy
import inspect
from collections.abc import AsyncGenerator, Awaitable, Callable, Generator, Iterable, Iterator
from contextvars import ContextVar
from string.templatelib import Template
from typing import ClassVar, NoReturn, overload

from .mappings import ClassList, DatasetMap, StyleMap, _snake_to_kebab
from .plugin import RenderContext
from .render import render_open_tag
from .tree import TreeNode
from .types import NodeContent


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


def _flatten_into(parent: TreeNode, items: Iterable) -> None:
    """Flatten an iterable of children directly into parent's children list."""
    children = parent.children
    for item in items:
        if item is None:
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
            _flatten_into(parent, item)
        else:
            node = Node.factory(item)
            node.parent_node = parent
            children.append(node)


def _convert_attribute_names(name: str) -> str:
    if name == "class_":
        return "class"
    return _snake_to_kebab(name)


class Fragment:
    """
    A document fragment — a builder wrapper around a DOM tree.
    Owns no rendering logic; use render()/stream()/astream() from the rendering module.
    """

    __slots__ = ("root", "append_pointer")

    root: TreeNode
    append_pointer: TreeNode

    def __init__(self, root: TreeNode, append_pointer: TreeNode, /):
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

    def __str__(self):
        from .rendering import render

        return render(self)

    def __iter__(self) -> Iterator[TreeNode | str | Template]:
        return iter(self.root.children)

    @overload
    def __rshift__(self, other: None) -> None: ...

    @overload
    def __rshift__(self, other: NodeContent) -> Fragment: ...

    def __rshift__(self, other):
        if other is None:
            return None

        if isinstance(other, str | Template):
            self.append_pointer.children.append(other)
            return self

        if isinstance(other, tuple | list):
            _flatten_into(self.append_pointer, other)
            return self

        if isinstance(other, Fragment):
            self.append(other)  # Fragment.append already clones via _copy_tree
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
                return root.clone_node(deep=True)  # type: ignore[return-value]
            return root  # type: ignore[return-value]
        if callable(contents):
            if inspect.iscoroutinefunction(contents):
                return Async(contents)
            return Lazy(contents)  # type: ignore[arg-type]
        raise ValueError(f"Unsupported type for >>: {type(contents)}")

    @overload
    def __rshift__(self, other: NodeContent) -> Fragment: ...

    @overload
    def __rshift__(self, other: None) -> None: ...

    def __rshift__(self, other):
        if other is None:
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
        from .rendering import render

        return render(self)

    def render_html(self, *, ctx: RenderContext | None = None) -> Generator[str]:
        from .rendering import stream_children

        yield from stream_children(self.children, ctx)

    async def arender_html(self, *, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        from .rendering import astream_children

        async for chunk in astream_children(self.children, ctx):
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

    def render_html(self, *, ctx: RenderContext | None = None) -> Generator[str]:
        yield f"<!--{self._escape_content()}-->"

    async def arender_html(self, *, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        yield f"<!--{self._escape_content()}-->"


class Element(Node):
    """An HTML Element with tag, attributes, and builder support."""

    __slots__ = ("attributes", "_style", "_class_list", "_dataset")

    tag: ClassVar[str]
    void: ClassVar[bool] = False
    attributes: dict[str, object]

    def __init__(self, attributes: dict[str, object] | None = None, /, **keyword_attributes: object):
        super().__init__()
        merged: dict[str, object] = {k.lower(): v for k, v in attributes.items()} if attributes else {}
        for k, v in keyword_attributes.items():
            merged[_convert_attribute_names(k)] = v
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
                if isinstance(child, TreeNode):
                    new_obj.append_child(copy.replace(child))
                else:
                    new_obj.children.append(child)
        return new_obj

    @property
    def tag_name(self) -> str:
        """The tag name of this element."""
        return self.tag

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

    def render_html(
        self,
        *,
        ctx: RenderContext | None = None,
        before_close: Callable[[], Generator[str]] | None = None,
    ) -> Generator[str]:
        from .rendering import stream_children

        attrs = self._render_attrs()
        if self.void:
            yield render_open_tag(self.tag, attrs, void=True)
        else:
            yield render_open_tag(self.tag, attrs)
            yield from stream_children(self.children, ctx)
            if before_close is not None:
                yield from before_close()
            yield f"</{self.tag}>"

    async def arender_html(
        self,
        *,
        ctx: RenderContext | None = None,
        before_close: Callable[[], AsyncGenerator[str]] | None = None,
    ) -> AsyncGenerator[str]:
        from .rendering import astream_children

        attrs = self._render_attrs()
        if self.void:
            yield render_open_tag(self.tag, attrs, void=True)
        else:
            yield render_open_tag(self.tag, attrs)
            async for chunk in astream_children(self.children, ctx):
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
    __slots__ = ("loading", "slot_name")

    def __init__(
        self,
        child: Node | Fragment,
        *,
        slot_name: str,
        loading: str | Template | Node | None = None,
    ):
        super().__init__()
        if loading is not None and not isinstance(loading, str | Template):
            self.loading: str | Template | Node | None = Node.factory(loading)
        else:
            self.loading = loading
        self.slot_name = slot_name

        if isinstance(child, Fragment):
            self.append_child(child.root)
        elif isinstance(child, Node):
            self.append_child(child)
        else:
            raise ValueError(f"Deferred can only be initialized with a Node or Fragment, not {type(child)}")

    def __replace__(self, /, **changes):
        child = self.children[0]
        assert isinstance(child, TreeNode)
        return type(self)(copy.replace(child), slot_name=self.slot_name, loading=self.loading)

    def render_html(self, *, ctx: RenderContext | None = None) -> Generator[str]:
        raise TypeError("Deferred nodes require DeferPlugin")

    async def arender_html(self, *, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
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

    def render_html(self, *, ctx: RenderContext | None = None) -> Generator[str]:
        from .rendering import render_result

        yield from render_result(self.fn(), ctx)

    async def arender_html(self, *, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        from .rendering import arender_result

        async for chunk in arender_result(self.fn(), ctx):
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

    def render_html(self, *, ctx: RenderContext | None = None) -> Generator[str]:
        raise TypeError("Async nodes require async rendering")

    async def arender_html(self, *, ctx: RenderContext | None = None) -> AsyncGenerator[str]:
        from .rendering import arender_result

        async for chunk in arender_result(await self.fn(), ctx):
            yield chunk


_MISSING = object()

_render_vars: ContextVar[dict[str, object] | None] = ContextVar("shifthtml.render_vars", default=None)


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

    def __call__(self) -> object:
        vars = _render_vars.get()
        if vars and self.name in vars:
            return vars[self.name]
        if self.default is not _MISSING:
            return self.default
        raise LookupError(f"Var {self.name!r} not set")

    def __repr__(self) -> str:
        return f"Var({self.name!r})"


class _VarNamespace:
    """Attribute-access shorthand for creating Var instances: ``args.title`` → ``Var("title")``."""

    __slots__ = ()

    def __getattr__(self, name: str) -> Var:
        return Var(name)

    def __repr__(self) -> str:
        return "args"


args = _VarNamespace()
