from shifthtml import (
    div,
    footer,
    h1,
    header,
    li,
    main,
    p,
    span,
    ul,
)
from shifthtml.defer import defer


def test_render_deferred_paragraph():
    tag = div() >> (
        p() >> "Paragraph 1",
        defer("para-2", p() >> "Paragraph 2", loading="Loading..."),
        p() >> "Paragraph 3",
    )
    assert tag.render() == (
        '<div><p>Paragraph 1</p><div id="para-2">Loading...</div><p>Paragraph 3</p>'
        '<shift-update action="replace" target="para-2">'
        "<template><p>Paragraph 2</p></template><shift-done></shift-done></shift-update></div>"
    )


def test_render_deferred_list_and_nested_items():
    tag = div() >> (
        header() >> h1() >> "Deferred streaming",
        main()
        >> defer(
            "list",
            ul() >> (li() >> defer(f"item-{x}", span() >> f"Item {x}", loading="Loading...") for x in range(3)),
            loading="Loading...",
        ),
        footer() >> "Footer content",
    )
    assert tag.render() == (
        "<div><header><h1>Deferred streaming</h1></header>"
        '<main><div id="list">Loading...</div></main>'
        "<footer>Footer content</footer>"
        '<shift-update action="replace" target="list"><template>'
        "<ul>"
        '<li><div id="item-0">Loading...</div></li>'
        '<li><div id="item-1">Loading...</div></li>'
        '<li><div id="item-2">Loading...</div></li>'
        "</ul></template><shift-done></shift-done></shift-update>"
        '<shift-update action="replace" target="item-0">'
        "<template><span>Item 0</span></template><shift-done></shift-done></shift-update>"
        '<shift-update action="replace" target="item-1">'
        "<template><span>Item 1</span></template><shift-done></shift-done></shift-update>"
        '<shift-update action="replace" target="item-2">'
        "<template><span>Item 2</span></template><shift-done></shift-done></shift-update>"
        "</div>"
    )
