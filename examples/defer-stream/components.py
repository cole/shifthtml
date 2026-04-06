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

LOREM_3 = (
    "Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, "
    "consectetur, adipisci velit, sed quia non numquam eius modi tempora "
    "incidunt ut labore et dolore magnam aliquam quaerat voluptatem."
)

LOREM_4 = (
    "Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis "
    "suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur? Quis "
    "autem vel eum iure reprehenderit qui in ea voluptate velit esse quam "
    "nihil molestiae consequatur, vel illum qui dolorem eum fugiat."
)

LOREM_5 = (
    "At vero eos et accusamus et iusto odio dignissimos ducimus qui "
    "blanditiis praesentium voluptatum deleniti atque corrupti quos "
    "dolores et quas molestias excepturi sint occaecati cupiditate non "
    "provident, similique sunt in culpa qui officia deserunt mollitia "
    "animi, id est laborum et dolorum fuga."
)

LOREM_6 = (
    "Et harum quidem rerum facilis est et expedita distinctio. Nam libero "
    "tempore, cum soluta nobis est eligendi optio cumque nihil impedit "
    "quo minus id quod maxime placeat facere possimus, omnis voluptas "
    "assumenda est, omnis dolor repellendus."
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


def _deferred_paragraph(col: int, index: int, text: str):
    def render():
        sleep(2)
        return text

    return defer(f"col-{col}-p{index}", p() >> render, loading="Loading…")


def col1_content():
    sleep(2)
    return (
        h2() >> "Column 1",
        p() >> LOREM_1,
        _deferred_paragraph(1, 2, LOREM_3),
        _deferred_paragraph(1, 3, LOREM_4),
        _deferred_paragraph(1, 4, LOREM_5),
    )


def col2_content():
    sleep(5)
    return (
        h2() >> "Column 2",
        p() >> LOREM_2,
        _deferred_paragraph(2, 2, LOREM_3),
        _deferred_paragraph(2, 3, LOREM_5),
        _deferred_paragraph(2, 4, LOREM_6),
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
