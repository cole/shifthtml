from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .element import Element


class CSSStyleDeclaration:
    """Inline style API, like DOM's CSSStyleDeclaration."""

    _properties: dict[str, str]
    _owner: Element | None

    def __init__(self, *, owner: Element | None = None):
        super().__setattr__("_properties", {})
        super().__setattr__("_owner", owner)

    def __setattr__(self, name: str, value: str) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
        elif name == "css_text":
            type(self).css_text.fset(self, value)
        else:
            self._properties[name.replace("_", "-")] = value

    def __getattr__(self, name: str) -> str:
        return self._properties.get(name.replace("_", "-"), "")

    def __delattr__(self, name: str) -> None:
        self._properties.pop(name.replace("_", "-"), None)

    def set_property(self, name: str, value: str) -> None:
        self._properties[name] = value

    def get_property_value(self, name: str) -> str:
        return self._properties.get(name, "")

    def remove_property(self, name: str) -> str:
        return self._properties.pop(name, "")

    @property
    def css_text(self) -> str:
        return "; ".join(f"{k}: {v}" for k, v in self._properties.items())

    @css_text.setter
    def css_text(self, value: str) -> None:
        self._properties.clear()
        for part in value.split(";"):
            part = part.strip()
            if ":" in part:
                k, v = part.split(":", 1)
                self._properties[k.strip()] = v.strip()

    @property
    def length(self) -> int:
        return len(self._properties)
