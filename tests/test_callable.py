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


def test_render_single_node_callable():
    def user_avatar():
        return img(id="photo", src="https://example.com/photo.jpg")

    tag = shift(
        div >> user_avatar,
    )

    assert (
        str(tag)
        == '<div><img id="photo" src="https://example.com/photo.jpg" /></div>'
    )


def test_render_callable_in_sequence():
    def user_avatar():
        return img(id="photo", src="https://example.com/photo.jpg")

    tag = shift(
        div
        >> (
            p >> "text",
            user_avatar,
        )
    )

    assert (
        str(tag)
        == '<div><p>text</p><img id="photo" src="https://example.com/photo.jpg" /></div>'
    )


def test_render_single_callable_nested_return():
    def photo_component():
        return div @ {"id": "div2"} >> img(
            id="photo", src="https://example.com/photo.jpg"
        )

    tag = shift(
        div >> photo_component,
    )

    assert (
        str(tag)
        == '<div><div id="div2"><img id="photo" src="https://example.com/photo.jpg" /></div></div>'
    )
