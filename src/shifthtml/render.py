from collections.abc import Generator
from html import escape
from typing import Literal

from .compat import Interpolation, Template


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


def render_attributes(attributes: dict[str, str | Template]) -> Generator[str]:
    for key, value in attributes.items():
        value = attributes[key]
        if value is None:
            rendered_value = ""
        elif value is True:
            rendered_value = "true"
        elif value is False:
            rendered_value = "false"
        else:
            rendered_value = "".join(render_string(str(value), quote=True))

        yield f'{key}="{rendered_value}"'
