import inspect
from collections.abc import AsyncGenerator
from html import escape
from string.templatelib import Interpolation, Template

from .render import _convert


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
