import pytest
from django.db.models import Count
from django.test import RequestFactory
from library.models import Author, Book
from library.pages import (
    author_detail_page,
    author_form_page,
    author_list_page,
    book_detail_page,
    book_form_page,
    book_list_page,
    delete_page,
)
from library.views import author_list, book_list

from shifthtml import shift


def render(node) -> str:
    return str(shift(node))


@pytest.fixture()
def austen(db):
    return Author.objects.create(name="Jane Austen", born="1775-12-16", bio="English novelist.")


@pytest.fixture()
def pride(db, austen):
    return Book.objects.create(
        title="Pride and Prejudice",
        author=austen,
        published="1813-01-28",
        genre="Fiction",
        isbn="9780141439518",
    )


# ---- Author pages ----


@pytest.mark.django_db
def test_author_list_empty(snapshot):
    assert render(author_list_page([])) == snapshot


@pytest.mark.django_db
def test_author_list_with_data(snapshot, austen):
    authors = Author.objects.annotate(book_count=Count("books"))
    assert render(author_list_page(authors)) == snapshot


@pytest.mark.django_db
def test_author_list_search_no_results(snapshot):
    assert render(author_list_page([], search="missing")) == snapshot


@pytest.mark.django_db
def test_author_detail(snapshot, austen, pride):
    assert render(author_detail_page(austen, austen.books.all())) == snapshot


@pytest.mark.django_db
def test_author_form_new(snapshot):
    assert render(author_form_page()) == snapshot


@pytest.mark.django_db
def test_author_form_edit(snapshot, austen):
    assert render(author_form_page(austen)) == snapshot


# ---- Book pages ----


@pytest.mark.django_db
def test_book_list_empty(snapshot):
    assert render(book_list_page([])) == snapshot


@pytest.mark.django_db
def test_book_list_with_data(snapshot, pride):
    books = Book.objects.select_related("author")
    assert render(book_list_page(books)) == snapshot


@pytest.mark.django_db
def test_book_detail(snapshot, pride):
    book = Book.objects.select_related("author").get(pk=pride.pk)
    assert render(book_detail_page(book)) == snapshot


@pytest.mark.django_db
def test_book_form_new(snapshot, austen):
    assert render(book_form_page(Author.objects.all())) == snapshot


@pytest.mark.django_db
def test_book_form_edit(snapshot, austen, pride):
    assert render(book_form_page(Author.objects.all(), pride)) == snapshot


# ---- Delete page ----


def test_delete_page(snapshot):
    assert render(delete_page("Author", "Jane Austen", "/authors/1/delete/", "/authors/")) == snapshot


# ---- View integration ----


@pytest.mark.django_db
def test_author_list_view(snapshot, austen):
    request = RequestFactory().get("/authors/")
    html = b"".join(author_list(request).streaming_content).decode()
    assert html == snapshot


@pytest.mark.django_db
def test_book_list_view(snapshot, pride):
    request = RequestFactory().get("/books/")
    html = b"".join(book_list(request).streaming_content).decode()
    assert html == snapshot
