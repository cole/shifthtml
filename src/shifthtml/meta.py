from .node import HTMLElement, NodeContent


class TagMeta(type):
    def __new__(mcls, name: str, bases: tuple[type, ...], attrs: dict[str, object]) -> type:
        if "tag" not in attrs:
            raise ValueError(f"{name} must define a 'tag' class attribute")
        if not isinstance(attrs["tag"], str):
            raise TypeError(f"{name}.tag must be a string")

        return super().__new__(mcls, name, bases, attrs)

    def __rshift__(self, other: NodeContent) -> HTMLElement:
        return self() >> other
