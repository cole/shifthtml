from django.db.models import Count
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect

from shifthtml import shift

from . import components
from .models import Author, Book


def stream(page):
    return StreamingHttpResponse(shift(page).render(), content_type="text/html; charset=utf-8")


def index(request):
    return redirect("book_list")


# ---- Authors ----


def author_list(request):
    q = request.GET.get("q", "")
    authors = Author.objects.annotate(book_count=Count("books"))
    if q:
        authors = authors.filter(name__icontains=q)
    return stream(components.author_list_page(authors, search=q, message=request.GET.get("msg", "")))


def author_detail(request, pk):
    author = get_object_or_404(Author, pk=pk)
    return stream(components.author_detail_page(author, author.books.all()))


def author_create(request):
    if request.method == "POST":
        Author.objects.create(
            name=request.POST["name"],
            bio=request.POST.get("bio", ""),
            born=request.POST.get("born") or None,
        )
        return redirect("/authors/?msg=Author+created")
    return stream(components.author_form_page())


def author_edit(request, pk):
    author = get_object_or_404(Author, pk=pk)
    if request.method == "POST":
        author.name = request.POST["name"]
        author.bio = request.POST.get("bio", "")
        author.born = request.POST.get("born") or None
        author.save()
        return redirect("/authors/?msg=Author+updated")
    return stream(components.author_form_page(author))


def author_delete(request, pk):
    author = get_object_or_404(Author, pk=pk)
    if request.method == "POST":
        author.delete()
        return redirect("/authors/?msg=Author+deleted")
    return stream(components.delete_page("Author", author.name, f"/authors/{pk}/delete/", "/authors/"))


# ---- Books ----


def book_list(request):
    q = request.GET.get("q", "")
    books = Book.objects.select_related("author")
    if q:
        books = books.filter(title__icontains=q)
    return stream(components.book_list_page(books, search=q, message=request.GET.get("msg", "")))


def book_detail(request, pk):
    book = get_object_or_404(Book.objects.select_related("author"), pk=pk)
    return stream(components.book_detail_page(book))


def book_create(request):
    if request.method == "POST":
        Book.objects.create(
            title=request.POST["title"],
            author_id=request.POST["author"],
            published=request.POST.get("published") or None,
            isbn=request.POST.get("isbn", ""),
            genre=request.POST.get("genre", ""),
            summary=request.POST.get("summary", ""),
        )
        return redirect("/books/?msg=Book+created")
    return stream(components.book_form_page(Author.objects.all()))


def book_edit(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == "POST":
        book.title = request.POST["title"]
        book.author_id = request.POST["author"]
        book.published = request.POST.get("published") or None
        book.isbn = request.POST.get("isbn", "")
        book.genre = request.POST.get("genre", "")
        book.summary = request.POST.get("summary", "")
        book.save()
        return redirect("/books/?msg=Book+updated")
    return stream(components.book_form_page(Author.objects.all(), book))


def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == "POST":
        book.delete()
        return redirect("/books/?msg=Book+deleted")
    return stream(components.delete_page("Book", book.title, f"/books/{pk}/delete/", "/books/"))
