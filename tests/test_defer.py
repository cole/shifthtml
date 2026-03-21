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
        str(tag) == '<div><p>Paragraph 1</p><div id="p:para-2">Loading...</div><p>Paragraph 3</p>'
        '<script>document.getElementById("p:para-2").outerHTML=`<p>Paragraph 2<\\/p>`</script></div>'
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
    assert (
        str(tag) == "<div><header><h1>Deferred streaming</h1></header>"
        '<main><div id="p:list">Loading...</div></main>'
        "<footer>Footer content</footer>"
        '<script>document.getElementById("p:list").outerHTML=`<ul><li><div id="p:item-0">Loading...<\\/div><\\/li>'
        '<li><div id="p:item-1">Loading...<\\/div><\\/li>'
        '<li><div id="p:item-2">Loading...<\\/div><\\/li><\\/ul>`</script>'
        '<script>document.getElementById("p:item-0").outerHTML=`<span>Item 0<\\/span>`</script>'
        '<script>document.getElementById("p:item-1").outerHTML=`<span>Item 1<\\/span>`</script>'
        '<script>document.getElementById("p:item-2").outerHTML=`<span>Item 2<\\/span>`</script>'
        "</div>"
    )
