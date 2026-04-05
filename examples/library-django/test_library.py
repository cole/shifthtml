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
    assert author_list_page([]).render() == snapshot


@pytest.mark.django_db
def test_author_list_with_data(snapshot, austen):
    authors = Author.objects.annotate(book_count=Count("books"))
    assert author_list_page(authors).render() == snapshot


@pytest.mark.django_db
def test_author_list_search_no_results(snapshot):
    assert author_list_page([], search="missing").render() == snapshot


@pytest.mark.django_db
def test_author_detail(snapshot, austen, pride):
    assert author_detail_page(austen, austen.books.all()).render() == snapshot


@pytest.mark.django_db
def test_author_form_new(snapshot):
    assert author_form_page().render() == snapshot


@pytest.mark.django_db
def test_author_form_edit(snapshot, austen):
    assert author_form_page(austen).render() == snapshot


# ---- Book pages ----


@pytest.mark.django_db
def test_book_list_empty(snapshot):
    assert book_list_page([]).render() == snapshot


@pytest.mark.django_db
def test_book_list_with_data(snapshot, pride):
    books = Book.objects.select_related("author")
    assert book_list_page(books).render() == snapshot


@pytest.mark.django_db
def test_book_detail(snapshot, pride):
    book = Book.objects.select_related("author").get(pk=pride.pk)
    assert book_detail_page(book).render() == snapshot


@pytest.mark.django_db
def test_book_form_new(snapshot, austen):
    assert book_form_page(Author.objects.all()).render() == snapshot


@pytest.mark.django_db
def test_book_form_edit(snapshot, austen, pride):
    assert book_form_page(Author.objects.all(), pride).render() == snapshot


# ---- Delete page ----


def test_delete_page(snapshot):
    assert delete_page("Author", "Jane Austen", "/authors/1/delete/", "/authors/").render() == snapshot


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
