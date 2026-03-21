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
    meta,
    ol,
    p,
    script,
    section,
    span,
    style,
    title,
)
from shifthtml.defer import defer

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

CSS = """\
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: system-ui, -apple-system, sans-serif;
    background: #f0f2f5;
    min-height: 100vh;
}
.page-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 32px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.page-header h1 { font-size: 2rem; font-weight: 600; }
.columns {
    display: flex;
    gap: 16px;
    padding: 24px;
    max-width: 1400px;
    margin: 0 auto;
}
.col {
    flex: 1;
    background: white;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.col h2 { font-size: 1.25rem; margin-bottom: 16px; color: #1a1a2e; }
.col p { line-height: 1.7; color: #4a4a4a; }
.list-col { max-height: calc(100vh - 144px); overflow-y: auto; }
.list-col ol { padding-left: 24px; }
.list-col li { padding: 8px 4px; border-bottom: 1px solid #f0f0f0; color: #333; }
.list-col li:last-child { border-bottom: none; }
"""


def page(slot_filler_src: str):
    return html(lang="en") >> (
        page_head(),
        body >> (
            script(src=slot_filler_src),
            header(classname="page-header") >> h1 >> "Defer Stream Demo",
            div(id="content") >> defer(
                "body-content",
                columns(),
                loading="Loading body content...",
            ),
        ),
    )


def page_head():
    return head >> (
        meta(charset="UTF-8"),
        meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        title >> "Defer Stream Demo",
        style >> CSS,
    )


def columns():
    return section(classname="columns") >> (
        div(classname="col") >> defer(
            "col-1",
            div >> col1_content,
            loading="Loading column 1...",
        ),
        div(classname="col") >> defer(
            "col-2",
            div >> col2_content,
            loading="Loading column 2...",
        ),
        div(classname="col list-col") >> defer(
            "col-3",
            div >> col3_content,
            loading="Loading list...",
        ),
    )


def col1_content():
    sleep(2)
    return (
        h2 >> "Column 1",
        p >> LOREM_1,
    )


def col2_content():
    sleep(5)
    return (
        h2 >> "Column 2",
        p >> LOREM_2,
    )


def col3_content():
    return (
        h2 >> "100 Items",
        ol >> [
            li >> defer(
                f"item-{i}",
                span >> make_item(i),
                loading="...",
            )
            for i in range(100)
        ],
    )


def make_item(i):
    def render():
        sleep(1)
        return f"Item {i + 1}"

    return render
