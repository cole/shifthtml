from html import escape
from typing import Literal, Generator

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
