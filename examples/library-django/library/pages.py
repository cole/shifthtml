from shifthtml import (
    a,
    button,
    div,
    form,
    h1,
    h2,
    input_,
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
    tr,
)

from .components import (
    detail_grid,
    empty,
    field,
    form_actions,
    layout,
    page_header,
    page_header_detail,
    search_form,
)

# ---- Author pages ----


def author_list_page(authors, *, search="", message=""):
    rows = [
        tr
        >> (
            td >> (a(href=f"/authors/{au.id}/") >> au.name),
            td >> (str(au.born) if au.born else "—"),
            td >> (span(class_="badge") >> str(au.book_count)),
            td(class_="row-actions")
            >> (
                a(href=f"/authors/{au.id}/edit/", class_="btn btn-sm") >> "Edit",
                a(href=f"/authors/{au.id}/delete/", class_="btn btn-sm btn-danger") >> "Delete",
            ),
        )
        for au in authors
    ]

    head_row = tr >> (th >> "Name", th >> "Born", th >> "Books", th >> "")
    data_table = table(class_="data-table") >> (thead >> head_row, tbody >> rows)

    content = div(class_="card") >> [
        page_header("Authors", "/authors/new/", "Add Author"),
        search_form("/authors/", search),
        *([data_table] if rows else [empty("No authors found." if search else "No authors yet.")]),
    ]

    return layout("Authors", content, nav_active="authors", message=message)


def author_detail_page(author, books):
    book_rows = [
        tr
        >> (
            td >> (a(href=f"/books/{b.id}/") >> b.title),
            td >> (str(b.published) if b.published else "—"),
            td >> (b.genre or "—"),
        )
        for b in books
    ]

    info = detail_grid(
        [
            ("Born", str(author.born) if author.born else "—"),
            ("Biography", author.bio or "—"),
        ]
    )

    author_card = div(class_="card") >> (
        page_header_detail(author.name, f"/authors/{author.id}/edit/", f"/authors/{author.id}/delete/"),
        info,
    )

    head_row = tr >> (th >> "Title", th >> "Published", th >> "Genre")
    book_table = table(class_="data-table") >> (thead >> head_row, tbody >> book_rows)

    books_card = section(class_="card") >> [
        h2 >> f"Books ({len(book_rows)})",
        *([book_table] if book_rows else [empty("No books by this author.")]),
    ]

    content = div >> [author_card, books_card]
    return layout(author.name, content, nav_active="authors")


def author_form_page(author=None):
    editing = author is not None
    action = f"/authors/{author.id}/edit/" if editing else "/authors/new/"
    page_title = f"Edit {author.name}" if editing else "New Author"

    name_field = field(
        "Name",
        input_(type="text", name="name", value=author.name if editing else "", required=True),
    )
    born_field = field(
        "Born",
        input_(type="date", name="born", value=str(author.born) if editing and author.born else ""),
    )
    bio_field = field(
        "Biography",
        textarea(name="bio", rows="4") >> (author.bio if editing else ""),
    )

    content = div(class_="card") >> (
        h1 >> page_title,
        form(action=action, method="POST") >> (name_field, born_field, bio_field, form_actions("/authors/")),
    )

    return layout(page_title, content, nav_active="authors")


# ---- Book pages ----


def book_list_page(books, *, search="", message=""):
    rows = [
        tr
        >> (
            td >> (a(href=f"/books/{b.id}/") >> b.title),
            td >> (a(href=f"/authors/{b.author_id}/") >> b.author.name),
            td >> (str(b.published) if b.published else "—"),
            td >> (b.genre or "—"),
            td(class_="row-actions")
            >> (
                a(href=f"/books/{b.id}/edit/", class_="btn btn-sm") >> "Edit",
                a(href=f"/books/{b.id}/delete/", class_="btn btn-sm btn-danger") >> "Delete",
            ),
        )
        for b in books
    ]

    head_row = tr >> (th >> "Title", th >> "Author", th >> "Published", th >> "Genre", th >> "")
    data_table = table(class_="data-table") >> (thead >> head_row, tbody >> rows)

    content = div(class_="card") >> [
        page_header("Books", "/books/new/", "Add Book"),
        search_form("/books/", search),
        *([data_table] if rows else [empty("No books found." if search else "No books yet.")]),
    ]

    return layout("Books", content, nav_active="books", message=message)


def book_detail_page(book):
    info = detail_grid(
        [
            ("Author", a(href=f"/authors/{book.author_id}/") >> book.author.name),
            ("Published", str(book.published) if book.published else "—"),
            ("Genre", book.genre or "—"),
            ("ISBN", book.isbn or "—"),
            ("Summary", book.summary or "—"),
        ]
    )

    content = div(class_="card") >> (
        page_header_detail(book.title, f"/books/{book.id}/edit/", f"/books/{book.id}/delete/"),
        info,
    )

    return layout(book.title, content, nav_active="books")


def book_form_page(authors, book=None):
    editing = book is not None
    action = f"/books/{book.id}/edit/" if editing else "/books/new/"
    page_title = f"Edit {book.title}" if editing else "New Book"

    author_options = [
        option(value=str(au.id), selected=(editing and book.author_id == au.id)) >> au.name for au in authors
    ]

    title_field = field(
        "Title",
        input_(type="text", name="title", value=book.title if editing else "", required=True),
    )
    author_field = field(
        "Author",
        select(name="author", required=True) >> [option(value="") >> "— Select author —", *author_options],
    )
    published_field = field(
        "Published",
        input_(
            type="date",
            name="published",
            value=str(book.published) if editing and book.published else "",
        ),
    )
    genre_field = field("Genre", input_(type="text", name="genre", value=book.genre if editing else ""))
    isbn_field = field("ISBN", input_(type="text", name="isbn", value=book.isbn if editing else "", maxlength="13"))
    summary_field = field("Summary", textarea(name="summary", rows="4") >> (book.summary if editing else ""))

    content = div(class_="card") >> (
        h1 >> page_title,
        form(action=action, method="POST")
        >> (
            title_field,
            author_field,
            published_field,
            genre_field,
            isbn_field,
            summary_field,
            form_actions("/books/"),
        ),
    )

    return layout(page_title, content, nav_active="books")


# ---- Delete ----


def delete_page(model_name, obj_name, action, cancel_url):
    confirmation = p >> (
        "Are you sure you want to delete ",
        strong >> obj_name,
        "? This cannot be undone.",
    )
    actions = div(class_="form-actions") >> (
        a(href=cancel_url, class_="btn") >> "Cancel",
        button(type="submit", class_="btn btn-danger") >> f"Delete {model_name}",
    )

    content = div(class_="card delete-confirm") >> (
        h1 >> f"Delete {model_name}",
        confirmation,
        form(action=action, method="POST") >> actions,
    )

    return layout(f"Delete {obj_name}", content)
