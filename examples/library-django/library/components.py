from shifthtml import (
    a,
    body,
    button,
    div,
    form,
    h1,
    head,
    header,
    html,
    input_,
    label,
    li,
    link,
    main,
    meta,
    nav,
    title,
    ul,
)

# ---- Layout ----


def layout(page_title, content, *, nav_active="", message=""):
    page = html(lang="en") >> (
        page_head(page_title),
        body
        >> [
            topbar(nav_active),
            main
            >> [
                *([alert(message)] if message else []),
                content,
            ],
        ],
    )
    return page


def page_head(page_title):
    return head >> (
        meta(charset="UTF-8"),
        meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        title >> f"{page_title} — Library",
        link(rel="stylesheet", href="/static/style.css"),
        link(rel="icon", href="data:,"),
    )


def topbar(active=""):
    links = [("books", "/books/", "Books"), ("authors", "/authors/", "Authors")]
    items = [li >> (a(href=url, classname="active" if key == active else "") >> lbl) for key, url, lbl in links]
    brand = a(href="/", classname="topbar-brand") >> "Library"

    return header(classname="topbar") >> (div(classname="topbar-inner") >> (brand, nav >> (ul >> items)),)


def alert(message):
    return div(classname="alert") >> message


# ---- Shared helpers ----


def page_header(heading, create_url, create_label):
    return div(classname="page-header") >> (
        h1 >> heading,
        a(href=create_url, classname="btn btn-primary") >> f"+ {create_label}",
    )


def page_header_detail(heading, edit_url, delete_url):
    actions = div(classname="header-actions") >> (
        a(href=edit_url, classname="btn btn-primary") >> "Edit",
        a(href=delete_url, classname="btn btn-danger") >> "Delete",
    )
    return div(classname="page-header") >> (h1 >> heading, actions)


def search_form(action, value=""):
    return form(action=action, method="GET", classname="search-form") >> (
        input_(type="search", name="q", placeholder="Search…", value=value),
        button(type="submit") >> "Search",
    )


def detail_grid(fields):
    return div(classname="detail-grid") >> [
        div(classname="detail-field")
        >> (
            div(classname="detail-label") >> lbl,
            div(classname="detail-value") >> val,
        )
        for lbl, val in fields
    ]


def field(label_text, input_el):
    return div(classname="form-group") >> (
        label >> label_text,
        input_el,
    )


def form_actions(cancel_url):
    return div(classname="form-actions") >> (
        a(href=cancel_url, classname="btn") >> "Cancel",
        button(type="submit", classname="btn btn-primary") >> "Save",
    )


def empty(text):
    return div(classname="empty-state") >> text
