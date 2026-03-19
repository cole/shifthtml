from shifthtml import (
    div,
    footer,
    h1,
    header,
    li,
    main,
    p,
    shift,
    span,
    ul,
)
from shifthtml.defer import defer


def test_render_deferred_paragraph():
    tag = shift(
        div
        >> (
            p >> "Paragraph 1",
            defer("para-2", p >> "Paragraph 2", loading="Loading..."),
            p >> "Paragraph 3",
        )
    )

    assert (
        str(tag)
        == '<div><p>Paragraph 1</p><template shadowrootmode="open"><slot name="para-2">Loading...</slot></template><p>Paragraph 3</p></div><p slot="para-2">Paragraph 2</p>'
    )


def test_render_deferred_list_and_nested_items():
    tag = shift(
        div
        >> (
            header >> h1 >> "Deferred streaming",
            main
            >> defer(
                "list",
                ul >> (li >> defer(f"item-{x}", span >> f"Item {x}", loading="Loading...") for x in range(3)),
                loading="Loading...",
            ),
            footer >> "Footer content",
        ),
    )
    # TODO: needs to handle deferred before body & preserve template context
    assert (
        str(tag)
        == '<div><header><h1>Deferred streaming</h1></header><main><template shadowrootmode="open"><slot name="list">Loading...</slot></template></main><footer>Footer content</footer></div><ul slot="list"><li><template shadowrootmode="open"><slot name="item-0">Loading...</slot></template></li><li><template shadowrootmode="open"><slot name="item-1">Loading...</slot></template></li><li><template shadowrootmode="open"><slot name="item-2">Loading...</slot></template></li></ul><span slot="item-0">Item 0</span><span slot="item-1">Item 1</span><span slot="item-2">Item 2</span>'
    )
