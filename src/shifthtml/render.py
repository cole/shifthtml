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
    if conversion == "s":
        return str(value)

    return str(value)


def render_template(template: Template, quote: bool = False) -> Generator[str]:
    for item in template:
        match item:
            case str() as s:
                yield s
            case Interpolation(value, _, conversion, format_spec):
                if callable(value):
                    value = value()
                value = _convert(value, conversion)
                value = format(value, format_spec)
                value = escape(value, quote=quote)

                yield value


def render_string(value: str | Template, quote: bool = True) -> Generator[str]:
    if isinstance(value, Template):
        yield from render_template(template=value, quote=quote)
    else:
        yield escape(value, quote=quote)


async def arender_template(template: Template, quote: bool = False) -> AsyncGenerator[str]:
    for item in template:
        match item:
            case str() as s:
                yield s
            case Interpolation(value, _, conversion, format_spec):
                if callable(value):
                    result = value()
                    if inspect.isawaitable(result):
                        value = await result
                    else:
                        value = result
                value = _convert(value, conversion)
                value = format(value, format_spec)
                value = escape(value, quote=quote)

                yield value


async def arender_string(value: str | Template, quote: bool = True) -> AsyncGenerator[str]:
    if isinstance(value, Template):
        async for chunk in arender_template(template=value, quote=quote):
            yield chunk
    else:
        yield escape(value, quote=quote)


def render_attributes(attributes: Mapping[str, object]) -> Generator[str]:
    for key, value in attributes.items():
        if value is None:
            rendered_value = ""
        elif value is True:
            rendered_value = "true"
        elif value is False:
            rendered_value = "false"
        elif isinstance(value, set | list | tuple):
            rendered_value = " ".join(
                "".join(render_string(v if isinstance(v, Template) else str(v), quote=True)) for v in value if v
            )
        else:
            rendered_value = "".join(render_string(value if isinstance(value, Template) else str(value), quote=True))

        yield f'{key}="{rendered_value}"'
