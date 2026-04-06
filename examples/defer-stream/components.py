import random
from time import sleep

from shifthtml import (
    body,
    div,
    h1,
    h2,
    head,
    header,
    html,
    li,
    link,
    meta,
    ol,
    p,
    section,
    span,
    title,
)
from shifthtml.defer import defer
from shifthtml.live import runtime

LOREM_1 = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
    "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
    "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris "
    "nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in "
    "reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla "
    "pariatur. Excepteur sint occaecat cupidatat non proident, sunt in "
    "culpa qui officia deserunt mollit anim id est laborum."
)

LOREM_2 = (
    "Sed ut perspiciatis unde omnis iste natus error sit voluptatem "
    "accusantium doloremque laudantium, totam rem aperiam, eaque ipsa "
    "quae ab illo inventore veritatis et quasi architecto beatae vitae "
    "dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit "
    "aspernatur aut odit aut fugit, sed quia consequuntur magni dolores "
    "eos qui ratione voluptatem sequi nesciunt."
)


def page():
    page_head = head() >> (
        meta(charset="UTF-8"),
        meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        title() >> "Defer Stream Demo",
        link(rel="stylesheet", href="/static/style.css"),
    )

    page_body = body() >> (
        header(class_="page-header") >> h1() >> "Defer Stream Demo",
        div(id="content") >> columns(),
        runtime(),
    )

    return html(lang="en") >> (page_head, page_body)


def columns():
    col1 = div(class_="col") >> defer(
        "col-1",
        div() >> col1_content,
        loading="Loading column 1...",
    )
    col2 = div(class_="col") >> defer(
        "col-2",
        div() >> col2_content,
        loading="Loading column 2...",
    )
    col3 = div(class_="col list-col") >> defer(
        "col-3",
        div() >> col3_content,
        loading="Loading list...",
    )

    return section(class_="columns") >> (col1, col2, col3)


def col1_content():
    sleep(2)
    return (
        h2() >> "Column 1",
        p() >> LOREM_1,
    )


def col2_content():
    sleep(5)
    return (
        h2() >> "Column 2",
        p() >> LOREM_2,
    )


def col3_content():
    items = [li() >> defer(f"item-{i}", span() >> make_item(i), loading="...") for i in range(100)]
    return (
        h2() >> "100 Items",
        ol() >> items,
    )


EMOJIS = [
    "🚀", "🎯", "🌟", "🔥", "💎", "🎨", "🌈", "⚡", "🍕", "🎸",
    "🐍", "🦀", "🌮", "🧩", "🎲", "🏆", "🌻", "🦊", "🍩", "🎭",
]


def make_item(i):
    def render():
        sleep(1)
        emoji = random.choice(EMOJIS)
        return f"{emoji} Item {i + 1}"

    return render
