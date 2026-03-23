from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .element import Element


def _snake_to_kebab(name: str) -> str:
    return name.replace("_", "-").lower()


class StyleMap:
    """Inline style API for elements."""

    _properties: dict[str, str]
    _owner: Element | None

    def __init__(self, *, owner: Element | None = None):
        super().__setattr__("_properties", {})
        super().__setattr__("_owner", owner)

    def _parse_css(self, value: str) -> None:
        self._properties.clear()
        for part in value.split(";"):
            part = part.strip()
            if ":" in part:
                k, v = part.split(":", 1)
                self._properties[k.strip()] = v.strip()

    def __setattr__(self, name: str, value: str) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
        elif name == "css_text":
            self._parse_css(value)
        else:
            self._properties[_snake_to_kebab(name)] = value

    def __getattr__(self, name: str) -> str:
        return self._properties.get(_snake_to_kebab(name), "")

    def __delattr__(self, name: str) -> None:
        self._properties.pop(_snake_to_kebab(name), None)

    def __setitem__(self, name: str, value: str) -> None:
        self._properties[name] = value

    def __getitem__(self, name: str) -> str:
        return self._properties[name]

    def __delitem__(self, name: str) -> None:
        del self._properties[name]

    def __contains__(self, name: str) -> bool:
        return name in self._properties

    def __iter__(self) -> Iterator[str]:
        return iter(self._properties)

    def __len__(self) -> int:
        return len(self._properties)

    def __str__(self) -> str:
        return self.css_text

    def __repr__(self) -> str:
        return f"StyleMap({self._properties!r})"

    def pop(self, name: str, default: str = "") -> str:
        return self._properties.pop(name, default)

    @property
    def css_text(self) -> str:
        return "; ".join(f"{k}: {v}" for k, v in self._properties.items())

    @css_text.setter
    def css_text(self, value: str) -> None:
        self._parse_css(value)


class ClassList:
    """Token list API for class management."""

    _owner: Element

    def __init__(self, *, owner: Element):
        self._owner = owner

    def _tokens(self) -> list[str]:
        raw = self._owner.attributes.get("class", "")
        if isinstance(raw, list):
            return [str(v) for v in raw]
        if isinstance(raw, tuple):
            return [str(v) for v in raw]
        if isinstance(raw, set):
            return sorted(str(v) for v in raw)
        if isinstance(raw, str):
            return raw.split() if raw else []
        return str(raw).split() if raw else []

    def _save(self, tokens: list[str]) -> None:
        self._owner.attributes["class"] = " ".join(tokens)

    def add(self, *tokens: str) -> None:
        current = self._tokens()
        for token in tokens:
            if token not in current:
                current.append(token)
        self._save(current)

    def remove(self, *tokens: str) -> None:
        current = self._tokens()
        for token in tokens:
            if token in current:
                current.remove(token)
        self._save(current)

    def toggle(self, token: str, force: bool | None = None) -> bool:
        current = self._tokens()
        present = token in current
        if force is None:
            force = not present
        if force:
            if not present:
                current.append(token)
        else:
            if present:
                current.remove(token)
        self._save(current)
        return force

    def replace(self, old: str, new: str) -> bool:
        current = self._tokens()
        if old not in current:
            return False
        idx = current.index(old)
        current[idx] = new
        self._save(current)
        return True

    def __iter__(self) -> Iterator[str]:
        return iter(self._tokens())

    def __len__(self) -> int:
        return len(self._tokens())

    def __contains__(self, token: str) -> bool:
        return token in self._tokens()

    def __str__(self) -> str:
        return " ".join(self._tokens())

    def __repr__(self) -> str:
        return f"ClassList({self._tokens()!r})"


class DatasetMap:
    """Data attribute access via element.dataset."""

    _owner: Element

    def __init__(self, *, owner: Element):
        super().__setattr__("_owner", owner)

    def __setattr__(self, name: str, value: str) -> None:
        self._owner.attributes[_snake_to_kebab("data-" + name)] = value

    def __getattr__(self, name: str) -> str:
        attr = _snake_to_kebab("data-" + name)
        value = self._owner.attributes.get(attr)
        if value is None:
            raise AttributeError(f"No data attribute '{attr}'")
        return str(value)

    def __delattr__(self, name: str) -> None:
        attr = _snake_to_kebab("data-" + name)
        if attr not in self._owner.attributes:
            raise AttributeError(f"No data attribute '{attr}'")
        del self._owner.attributes[attr]

    def __contains__(self, name: str) -> bool:
        return _snake_to_kebab("data-" + name) in self._owner.attributes

    def __iter__(self) -> Iterator[str]:
        return (k.removeprefix("data-").replace("-", "_") for k in self._owner.attributes if k.startswith("data-"))

    def __repr__(self) -> str:
        items = {
            k.removeprefix("data-").replace("-", "_"): v
            for k, v in self._owner.attributes.items()
            if k.startswith("data-")
        }
        return f"DatasetMap({items!r})"
