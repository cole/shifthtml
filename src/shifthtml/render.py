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
                    yield escape(v, quote=quote)
    else:
        yield escape(value, quote=quote)


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
                    yield escape(v, quote=quote)
    else:
        yield escape(value, quote=quote)


def render_attributes(attributes: Mapping[str, object]) -> Generator[str]:
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
    suffix = " />" if void else ">"
    if not attributes:
        return f"<{tag}{suffix}"
    attr_parts: list[str] = []
    for key, value in attributes.items():
        if value is None or value is False:
            continue
        if value is True:
            attr_parts.append(key)
        elif isinstance(value, str):
            attr_parts.append(f'{key}="{escape(value, quote=True)}"')
        elif isinstance(value, Template):
            rendered = "".join(render_string(value, quote=True))
            attr_parts.append(f'{key}="{rendered}"')
        elif isinstance(value, set | list | tuple):
            rendered = " ".join(
                "".join(render_string(v if isinstance(v, Template) else str(v), quote=True)) for v in value if v
            )
            attr_parts.append(f'{key}="{rendered}"')
        else:
            attr_parts.append(f'{key}="{escape(str(value), quote=True)}"')
    if not attr_parts:
        return f"<{tag}{suffix}"
    return f"<{tag} {' '.join(attr_parts)}{suffix}"


def render_string_to_list(value: str | Template, buf: list[str], quote: bool = False) -> None:
    """Append rendered string chunks directly to a list buffer."""
    if isinstance(value, Template):
        for item in value:
            match item:
                case str() as s:
                    buf.append(s)
                case Interpolation(v, _, conversion, format_spec):
                    if callable(v):
                        v = v()
                    v = _convert(v, conversion)
                    v = format(v, format_spec)
                    buf.append(escape(v, quote=quote))
    else:
        buf.append(escape(value, quote=quote))
