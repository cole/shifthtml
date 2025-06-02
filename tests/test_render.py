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
    tag = shift(
        h1 >> "Hello, World!"
    )

    assert tag.render() == "<h1>Hello, World!</h1>"


def test_render_h1_template():
    place = "World"
    tag = shift(
        h1 >> f"Hello, {place}!"
    )

    assert tag.render() == "<h1>Hello, World!</h1>"


def test_render_h1_attributes():
    tag = shift(
        h1(id="bighead") >> "Hello, World!"
    )

    assert tag.render() == '<h1 id="bighead">Hello, World!</h1>'


def test_render_h1_dynamic_attribute_value():
    element_id = "testing"
    tag = shift(
        h1(id=f"{element_id}") >> "Hello, World!"
    )

    assert tag.render() == '<h1 id="testing">Hello, World!</h1>'


def test_render_h1_dynamic_attribute_name():
    attr_name = "my-test-attr"
    tag = shift(
        h1(**{ attr_name: "foo" }) >> "Hello, World!"
    )

    assert tag.render() == '<h1 my-test-attr="foo">Hello, World!</h1>'


def test_render_ul():
    tag = shift(
        ul >> (
            li >> "Test",
            li >> "one",
            li >> "two"
        )
    )

    assert tag.render() == '<ul><li>Test</li><li>one</li><li>two</li></ul>'



def test_render_img_attributes_as_keywords():
    tag = shift(
        img(id="photo", src="https://example.com/photo.jpg")
    )

    assert tag.render() == '<img id="photo" src="https://example.com/photo.jpg" />'


def test_render_img_attributes_with_dict():
    tag = shift(
        img @ {"id": "photo", "src": "https://example.com/photo.jpg"}
    )

    assert tag.render() == '<img id="photo" src="https://example.com/photo.jpg" />'


def test_render_img_child_errors():
    with pytest.raises(ValueError):
        shift(
            img(id="photo", src="https://example.com/photo.jpg") >> "test"
        )


def test_render_nesting():
    count = 1
    tag = shift(
        html >> body @ { "class": "test", "data-testid": f"body-{count}" } >> div >> (
            h1 >> "Welcome to the Test Page",
            p >> "This is a paragraph on the test page."
        )
    )

    assert tag.render() == '<html><body class="test" data-testid="body-1"><div><h1>Welcome to the Test Page</h1><p>This is a paragraph on the test page.</p></div></body></html>'


def test_render_head_tag():
    tag = shift(
        head >> (
            title >> "Test Page",
            meta(charset="UTF-8"),
            link(rel="stylesheet", href="style.css"),
            style >> "body { background-color: #fff; }"
        )
    )

    assert tag.render() == '<head><title>Test Page</title><meta charset="UTF-8" /><link rel="stylesheet" href="style.css" /><style>body { background-color: #fff; }</style></head>'


def test_render_multiple_vars():
    tag1 = shift(
        div >> (
            p >> "paragraph 1",
            p >> "paragraph 1.5",
        )
    )
    tag2 = shift(
        div >> p >> "paragraph 2"
    )

    main_tag = shift(
        main >> (
            tag1,
            aside >> tag2,
            div(classname="test") >> tag2,
        )
    )

    assert main_tag.render() == '<main><div><p>paragraph 1</p><p>paragraph 1.5</p></div><aside><div><p>paragraph 2</p></div></aside><div class="test"><div><p>paragraph 2</p></div></div></main>'

