from __future__ import annotations

from collections.abc import AsyncGenerator, Callable, Generator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    import anyio

    from .tree import Node


@runtime_checkable
class Plugin(Protocol):
    """Protocol for shifthtml plugins.

    Required hooks:
        pre_render_node(node, stream, ctx) — intercept or observe a node before rendering.
            ``stream`` is a callable that renders a node through the full plugin pipeline.
            Return a Generator to override, or None to pass through.
        post_render(ctx) — emit content after the full tree has rendered.

    Optional hooks (checked via getattr):
        pre_render(ctx)  — emit content before the tree renders.
        post_render_node(node, ctx) — emit content or observe after a node has rendered.
        apre_render_node / apost_render_node / apre_render / apost_render
                         — async variants; sync hooks are used as fallback.
    """

    def pre_render_node(
        self,
        node: Node,
        stream: StreamFn,
        ctx: RenderContext,
    ) -> Generator[str] | None: ...

    def post_render(self, ctx: RenderContext) -> Generator[str]: ...


type StreamFn = Callable[[Node], Generator[str]]
type AStreamFn = Callable[[Node], AsyncGenerator[str]]


_registry: dict[type, Plugin] = {}


def register(plugin: Plugin) -> None:
    _registry[type(plugin)] = plugin


_EMPTY_PLUGINS: tuple[Plugin, ...] = ()


def registered_plugins() -> tuple[Plugin, ...]:
    return tuple(_registry.values()) if _registry else _EMPTY_PLUGINS


def clear_registry() -> None:
    _registry.clear()


@dataclass(slots=True)
class RenderContext:
    plugins: tuple[Plugin, ...]
    state: dict[Any, Any] = field(default_factory=dict)
    cancel_scope: anyio.CancelScope | None = None
    max_depth: int = 100
    max_nodes: int | None = None
    _depth: int = field(default=0, repr=False)
    _node_count: int = field(default=0, repr=False)

    def _post_render_node(self, node: Node) -> Generator[str]:
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

    async def _apost_render_node(self, node: Node) -> AsyncGenerator[str]:
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
