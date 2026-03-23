from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    import anyio

    from .tree import TreeNode


@runtime_checkable
class Plugin(Protocol):
    """Protocol for shifthtml plugins.

    Required hooks:
        pre_render_node  — intercept or observe a node before rendering.
                           Return a Generator to override, or None to pass through.
        post_render      — emit content after the full tree has rendered.

    Optional hooks (checked via getattr):
        pre_render       — emit content before the tree renders.
        post_render_node — emit content or observe after a node has rendered.
        apre_render_node / apost_render_node / apre_render / apost_render
                         — async variants; sync hooks are used as fallback.
    """

    def pre_render_node(self, node: TreeNode, ctx: RenderContext) -> Generator[str] | None: ...

    def post_render(self, ctx: RenderContext) -> Generator[str]: ...


_registry: dict[type, Plugin] = {}


def register(plugin: Plugin) -> None:
    _registry[type(plugin)] = plugin


def registered_plugins() -> tuple[Plugin, ...]:
    return tuple(_registry.values())


def clear_registry() -> None:
    _registry.clear()


@dataclass
class RenderContext:
    plugins: tuple[Plugin, ...]
    state: dict[Any, Any] = field(default_factory=dict)
    cancel_scope: anyio.CancelScope | None = None

    # -- sync --

    def render_node(self, node: TreeNode) -> Generator[str]:
        for plugin in self.plugins:
            result = plugin.pre_render_node(node, self)
            if result is not None:
                yield from result
                yield from self._post_render_node(node)
                return

        yield from node.render_html(ctx=self)
        yield from self._post_render_node(node)

    def _post_render_node(self, node: TreeNode) -> Generator[str]:
        for plugin in self.plugins:
            hook = getattr(plugin, "post_render_node", None)
            if hook is not None:
                result = hook(node, self)
                if result is not None:
                    yield from result

    def pre_render_all(self) -> Generator[str]:
        for plugin in self.plugins:
            hook = getattr(plugin, "pre_render", None)
            if hook is not None:
                yield from hook(self)

    def post_render_all(self) -> Generator[str]:
        for plugin in self.plugins:
            yield from plugin.post_render(self)

    # -- async --

    async def arender_node(self, node: TreeNode) -> AsyncGenerator[str]:
        for plugin in self.plugins:
            ahook = getattr(plugin, "apre_render_node", None)
            result = ahook(node, self) if ahook is not None else plugin.pre_render_node(node, self)

            if result is not None:
                if isinstance(result, AsyncGenerator):
                    async for chunk in result:
                        yield chunk
                else:
                    for chunk in result:
                        yield chunk
                async for chunk in self._apost_render_node(node):
                    yield chunk
                return

        async for chunk in node.arender_html(ctx=self):
            yield chunk
        async for chunk in self._apost_render_node(node):
            yield chunk

    async def _apost_render_node(self, node: TreeNode) -> AsyncGenerator[str]:
        for plugin in self.plugins:
            ahook = getattr(plugin, "apost_render_node", None)
            if ahook is not None:
                result = ahook(node, self)
                if result is not None:
                    async for chunk in result:
                        yield chunk
            else:
                hook = getattr(plugin, "post_render_node", None)
                if hook is not None:
                    result = hook(node, self)
                    if result is not None:
                        for chunk in result:
                            yield chunk

    async def apre_render_all(self) -> AsyncGenerator[str]:
        for plugin in self.plugins:
            ahook = getattr(plugin, "apre_render", None)
            if ahook is not None:
                async for chunk in ahook(self):
                    yield chunk
            else:
                hook = getattr(plugin, "pre_render", None)
                if hook is not None:
                    for chunk in hook(self):
                        yield chunk

    async def apost_render_all(self) -> AsyncGenerator[str]:
        for plugin in self.plugins:
            ahook = getattr(plugin, "apost_render", None)
            if ahook is not None:
                async for chunk in ahook(self):
                    yield chunk
            else:
                for chunk in plugin.post_render(self):
                    yield chunk
