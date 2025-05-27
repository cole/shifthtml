import pytest

from shifthtml import (
    html,
    head,
    body,
    base,
    link,
    meta,
    style,
    title,
    address,
    article,
    aside,
    footer,
    header,
    h1,
    h2,
    h3,
    h4,
    h5,
    h6,
    main,
    nav,
    section,
    blockquote,
    dd,
    div,
    dl,
    dt,
    figcaption,
    figure,
    hr,
    li,
    ol,
    p,
    pre,
    ul,
    a,
    abbr,
    b,
    bdi,
    bdo,
    br,
    cite,
    code,
    data,
    dfn,
    em,
    i,
    kbd,
    mark,
    q,
    rp,
    rt,
    ruby,
    s,
    samp,
    small,
    span,
    strong,
    sub,
    sup,
    time,
    u,
    var,
    wbr,
    del_,
    ins,
    area,
    audio,
    img,
    map_,
    track,
    video,
    embed,
    iframe,
    object_,
    picture,
    portal,
    source,
    canvas,
    noscript,
    script,
    del_,
    ins,
    caption,
    col,
    colgroup,
    table,
    tbody,
    td,
    tfoot,
    th,
    thead,
    tr,
    button,
    datalist,
    fieldset,
    form,
    input_,
    label,
    legend,
    meter,
    optgroup,
    option,
    output,
    progress,
    select,
    textarea,
    details,
    dialog,
    menu,
    summary,
    slot,
    template,
    shift,
)


def test_render_h1_string():
    tag = h1 >> "Hello, World!"

    assert shift(tag) == "<h1>Hello, World!</h1>"


def test_render_h1_template():
    place = "World"
    tag = h1 >> t"Hello, {place}!"

    assert shift(tag) == "<h1>Hello, World!</h1>"


def test_render_h1_attributes():
    tag = h1(id="bighead") >> "Hello, World!"

    assert shift(tag) == '<h1 id="bighead">Hello, World!</h1>'


def test_render_h1_dynamic_attribute_value():
    element_id = "testing"
    tag = h1(id=t"{element_id}") >> t"Hello, World!"

    assert shift(tag) == '<h1 id="testing">Hello, World!</h1>'


def test_render_h1_dynamic_attribute_name():
    attr_name = "my-test-attr"
    tag = h1(**{ attr_name: "foo" }) >> "Hello, World!"

    assert shift(tag) == '<h1 my-test-attr="foo">Hello, World!</h1>'


def test_render_ul():
    tag = (
        ul >> (
            li >> "Test",
            li >> "one",
            li >> "two"
        )
    )

    assert shift(tag) == '<ul><li>Test</li><li>one</li><li>two</li></ul>'



def test_render_img_attributes():
    tag = (
        img(id="photo", src="https://example.com/photo.jpg")
    )

    assert shift(tag) == '<img id="photo" src="https://example.com/photo.jpg" />'



def test_render_img_child_errors():
    with pytest.raises(ValueError):
        img(id="photo", src="https://example.com/photo.jpg") >> "test"


def test_render_nesting():
    tag = html >> body(classname="test") >> div >> (
        h1 >> "Welcome to the Test Page",
        p >> "This is a paragraph on the test page."
    )
    children = tag.children
    while children:
        print(children[0].tag)
        print(children[0].children)
        children = children[0].children

    assert shift(tag) == '<html><body class="test"><h1>Welcome to the Test Page</h1><p>This is a paragraph on the test page.</p></body></html>'


def test_render_head_tag():
    tag = head >> (
        title >> "Test Page",
        meta(charset="UTF-8"),
        link(rel="stylesheet", href="style.css"),
        style >> "body { background-color: #fff; }"
    )

    assert shift(tag) == '<head><title>Test Page</title><meta charset="UTF-8" /><link rel="stylesheet" href="style.css" /><style>body { background-color: #fff; }</style></head>'
