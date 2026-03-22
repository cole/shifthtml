from shifthtml import (
    a,
    body,
    button,
    div,
    form,
    h1,
    h2,
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
    option,
    p,
    section,
    select,
    span,
    strong,
    table,
    tbody,
    td,
    textarea,
    th,
    thead,
    title,
    tr,
    ul,
)

# ---- Layout ----


def layout(page_title, content, *, nav_active="", message=""):
    return html(lang="en") >> (
        _page_head(page_title),
        body
        >> [
            _topbar(nav_active),
            main
            >> [
                *([_alert(message)] if message else []),
                content,
            ],
        ],
    )


def _page_head(page_title):
    return head >> (
        meta(charset="UTF-8"),
        meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        title >> f"{page_title} \u2014 Library",
        link(rel="stylesheet", href="/static/style.css"),
        link(rel="icon", href="data:,"),
    )


def _topbar(active=""):
    links = [("books", "/books/", "Books"), ("authors", "/authors/", "Authors")]
    return header(classname="topbar") >> (
        div(classname="topbar-inner")
        >> (
            a(href="/", classname="topbar-brand") >> "Library",
            nav
            >> (
                ul
                >> [li >> (a(href=url, classname="active" if key == active else "") >> lbl) for key, url, lbl in links]
            ),
        ),
    )


def _alert(message):
    return div(classname="alert") >> message


# ---- Author pages ----


def author_list_page(authors, *, search="", message=""):
    rows = [
        tr
        >> (
            td >> (a(href=f"/authors/{au.id}/") >> au.name),
            td >> (str(au.born) if au.born else "\u2014"),
            td >> (span(classname="badge") >> str(au.book_count)),
            td(classname="row-actions")
            >> (
                a(href=f"/authors/{au.id}/edit/", classname="btn btn-sm") >> "Edit",
                a(href=f"/authors/{au.id}/delete/", classname="btn btn-sm btn-danger") >> "Delete",
            ),
        )
        for au in authors
    ]

    content = div(classname="card") >> [
        _page_header("Authors", "/authors/new/", "Add Author"),
        _search_form("/authors/", search),
        *(
            [
                table(classname="data-table")
                >> (
                    thead >> (tr >> (th >> "Name", th >> "Born", th >> "Books", th >> "")),
                    tbody >> rows,
                )
            ]
            if rows
            else [_empty("No authors found." if search else "No authors yet.")]
        ),
    ]

    return layout("Authors", content, nav_active="authors", message=message)


def author_detail_page(author, books):
    book_rows = [
        tr
        >> (
            td >> (a(href=f"/books/{b.id}/") >> b.title),
            td >> (str(b.published) if b.published else "\u2014"),
            td >> (b.genre or "\u2014"),
        )
        for b in books
    ]

    content = div >> [
        div(classname="card")
        >> (
            _page_header_detail(author.name, f"/authors/{author.id}/edit/", f"/authors/{author.id}/delete/"),
            _detail_grid(
                [
                    ("Born", str(author.born) if author.born else "\u2014"),
                    ("Biography", author.bio or "\u2014"),
                ]
            ),
        ),
        section(classname="card")
        >> [
            h2 >> f"Books ({len(book_rows)})",
            *(
                [
                    table(classname="data-table")
                    >> (
                        thead >> (tr >> (th >> "Title", th >> "Published", th >> "Genre")),
                        tbody >> book_rows,
                    )
                ]
                if book_rows
                else [_empty("No books by this author.")]
            ),
        ],
    ]

    return layout(author.name, content, nav_active="authors")


def author_form_page(author=None):
    editing = author is not None
    action = f"/authors/{author.id}/edit/" if editing else "/authors/new/"
    page_title = f"Edit {author.name}" if editing else "New Author"

    content = div(classname="card") >> (
        h1 >> page_title,
        form(action=action, method="POST")
        >> (
            _field("Name", input_(type="text", name="name", value=author.name if editing else "", required=True)),
            _field(
                "Born",
                input_(type="date", name="born", value=str(author.born) if editing and author.born else ""),
            ),
            _field("Biography", textarea(name="bio", rows="4") >> (author.bio if editing else "")),
            _form_actions("/authors/"),
        ),
    )

    return layout(page_title, content, nav_active="authors")


# ---- Book pages ----


def book_list_page(books, *, search="", message=""):
    rows = [
        tr
        >> (
            td >> (a(href=f"/books/{b.id}/") >> b.title),
            td >> (a(href=f"/authors/{b.author_id}/") >> b.author.name),
            td >> (str(b.published) if b.published else "\u2014"),
            td >> (b.genre or "\u2014"),
            td(classname="row-actions")
            >> (
                a(href=f"/books/{b.id}/edit/", classname="btn btn-sm") >> "Edit",
                a(href=f"/books/{b.id}/delete/", classname="btn btn-sm btn-danger") >> "Delete",
            ),
        )
        for b in books
    ]

    content = div(classname="card") >> [
        _page_header("Books", "/books/new/", "Add Book"),
        _search_form("/books/", search),
        *(
            [
                table(classname="data-table")
                >> (
                    thead >> (tr >> (th >> "Title", th >> "Author", th >> "Published", th >> "Genre", th >> "")),
                    tbody >> rows,
                )
            ]
            if rows
            else [_empty("No books found." if search else "No books yet.")]
        ),
    ]

    return layout("Books", content, nav_active="books", message=message)


def book_detail_page(book):
    content = div(classname="card") >> (
        _page_header_detail(book.title, f"/books/{book.id}/edit/", f"/books/{book.id}/delete/"),
        _detail_grid(
            [
                ("Author", a(href=f"/authors/{book.author_id}/") >> book.author.name),
                ("Published", str(book.published) if book.published else "\u2014"),
                ("Genre", book.genre or "\u2014"),
                ("ISBN", book.isbn or "\u2014"),
                ("Summary", book.summary or "\u2014"),
            ]
        ),
    )

    return layout(book.title, content, nav_active="books")


def book_form_page(authors, book=None):
    editing = book is not None
    action = f"/books/{book.id}/edit/" if editing else "/books/new/"
    page_title = f"Edit {book.title}" if editing else "New Book"

    author_options = [
        option(value=str(au.id), selected=(editing and book.author_id == au.id)) >> au.name for au in authors
    ]

    content = div(classname="card") >> (
        h1 >> page_title,
        form(action=action, method="POST")
        >> (
            _field(
                "Title",
                input_(type="text", name="title", value=book.title if editing else "", required=True),
            ),
            _field(
                "Author",
                select(name="author", required=True)
                >> [option(value="") >> "\u2014 Select author \u2014", *author_options],
            ),
            _field(
                "Published",
                input_(
                    type="date",
                    name="published",
                    value=str(book.published) if editing and book.published else "",
                ),
            ),
            _field("Genre", input_(type="text", name="genre", value=book.genre if editing else "")),
            _field("ISBN", input_(type="text", name="isbn", value=book.isbn if editing else "", maxlength="13")),
            _field("Summary", textarea(name="summary", rows="4") >> (book.summary if editing else "")),
            _form_actions("/books/"),
        ),
    )

    return layout(page_title, content, nav_active="books")


# ---- Delete ----


def delete_page(model_name, obj_name, action, cancel_url):
    content = div(classname="card delete-confirm") >> (
        h1 >> f"Delete {model_name}",
        p
        >> (
            "Are you sure you want to delete ",
            strong >> obj_name,
            "? This cannot be undone.",
        ),
        form(action=action, method="POST")
        >> (
            div(classname="form-actions")
            >> (
                a(href=cancel_url, classname="btn") >> "Cancel",
                button(type="submit", classname="btn btn-danger") >> f"Delete {model_name}",
            ),
        ),
    )

    return layout(f"Delete {obj_name}", content)


# ---- Shared helpers ----


def _page_header(heading, create_url, create_label):
    return div(classname="page-header") >> (
        h1 >> heading,
        a(href=create_url, classname="btn btn-primary") >> f"+ {create_label}",
    )


def _page_header_detail(heading, edit_url, delete_url):
    return div(classname="page-header") >> (
        h1 >> heading,
        div(classname="header-actions")
        >> (
            a(href=edit_url, classname="btn btn-primary") >> "Edit",
            a(href=delete_url, classname="btn btn-danger") >> "Delete",
        ),
    )


def _search_form(action, value=""):
    return form(action=action, method="GET", classname="search-form") >> (
        input_(type="search", name="q", placeholder="Search\u2026", value=value),
        button(type="submit") >> "Search",
    )


def _detail_grid(fields):
    return div(classname="detail-grid") >> [
        div(classname="detail-field")
        >> (
            div(classname="detail-label") >> lbl,
            div(classname="detail-value") >> val,
        )
        for lbl, val in fields
    ]


def _field(label_text, input_el):
    return div(classname="form-group") >> (
        label >> label_text,
        input_el,
    )


def _form_actions(cancel_url):
    return div(classname="form-actions") >> (
        a(href=cancel_url, classname="btn") >> "Cancel",
        button(type="submit", classname="btn btn-primary") >> "Save",
    )


def _empty(text):
    return div(classname="empty-state") >> text
