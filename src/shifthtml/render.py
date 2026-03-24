import inspect
from collections.abc import AsyncGenerator, Generator, Mapping
from html import escape
from string.templatelib import Interpolation, Template
from typing import Literal


def _convert(value: object, conversion: Literal["a", "r", "s"] | None) -> str:
    if conversion == "a":
        return ascii(value)
    if conversion == "r":
        return repr(value)
    return str(value)


def _needs_escape(value: str, quote: bool = False) -> bool:
    """Check if a string contains characters that need HTML escaping."""
    if "&" in value or "<" in value or ">" in value:
        return True
    return quote and ('"' in value or "'" in value)


def render_string(value: str | Template, quote: bool = False) -> Generator[str]:
    if isinstance(value, Template):
        for item in value:
            match item:
                case str() as s:
                    yield s
                case Interpolation(v, _, conversion, format_spec):
                    if callable(v):
                        v = v()
                    v = _convert(v, conversion)
                    v = format(v, format_spec)
                    yield escape(v, quote=quote) if _needs_escape(v, quote) else v
    else:
        yield escape(value, quote=quote) if _needs_escape(value, quote) else value


async def arender_string(value: str | Template, quote: bool = False) -> AsyncGenerator[str]:
    if isinstance(value, Template):
        for item in value:
            match item:
                case str() as s:
                    yield s
                case Interpolation(v, _, conversion, format_spec):
                    if callable(v):
                        result = v()
                        if inspect.isawaitable(result):
                            v = await result
                        else:
                            v = result
                    v = _convert(v, conversion)
                    v = format(v, format_spec)
                    yield escape(v, quote=quote) if _needs_escape(v, quote) else v
    else:
        yield escape(value, quote=quote) if _needs_escape(value, quote) else value


def _render_attributes(attributes: Mapping[str, object]) -> Generator[str]:
    for key, value in attributes.items():
        if value is None or value is False:
            continue
        if value is True:
            yield key
            continue
        if isinstance(value, set | list | tuple):
            rendered_value = " ".join(
                "".join(render_string(v if isinstance(v, Template) else str(v), quote=True)) for v in value if v
            )
        else:
            rendered_value = "".join(render_string(value if isinstance(value, Template) else str(value), quote=True))

        yield f'{key}="{rendered_value}"'


def render_open_tag(tag: str, attributes: Mapping[str, object], void: bool = False) -> str:
    parts = [f"<{tag}"]
    for attr in _render_attributes(attributes):
        parts.append(f" {attr}")
    parts.append(" />" if void else ">")
    return "".join(parts)
