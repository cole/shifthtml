from typing import Protocol

from .element import Fragment
from .types import NodeContent


class TagMeta(type(Protocol)):
    def __new__(mcls, name: str, bases: tuple[type, ...], attrs: dict[str, object]) -> type:
        if "tag" not in attrs:
            raise ValueError(f"{name} must define a 'tag' class attribute")
        if not isinstance(attrs["tag"], str):
            raise TypeError(f"{name}.tag must be a string")

        return super().__new__(mcls, name, bases, attrs)

    def __rshift__(self, other: NodeContent) -> Fragment:
        instance = self()
        fragment = Fragment(instance, instance) >> other
        return fragment
