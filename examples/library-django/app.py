# /// script
# dependencies = [
#   "django>=5.0",
#   "shifthtml",
# ]
# [tool.uv.sources]
# shifthtml = { path = "../.." }
# ///

import sys
from pathlib import Path

import django
from django.conf import settings

BASE_DIR = Path(__file__).resolve().parent

if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY="dev-only-not-secret",
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}},
        INSTALLED_APPS=["django.contrib.staticfiles", "library"],
        MIDDLEWARE=[],
        ROOT_URLCONF="library.urls",
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        STATIC_URL="/static/",
        STATICFILES_DIRS=[BASE_DIR / "static"],
        MIGRATION_MODULES={"library": None},
    )
    django.setup()


def seed():
    from library.models import Author, Book

    if Author.objects.exists():
        return

    austen = Author.objects.create(
        name="Jane Austen",
        born="1775-12-16",
        bio="English novelist known for her sharp social commentary and wit.",
    )
    orwell = Author.objects.create(
        name="George Orwell",
        born="1903-06-25",
        bio="English novelist and essayist, best known for his allegorical and dystopian works.",
    )
    marquez = Author.objects.create(
        name="Gabriel García Márquez",
        born="1927-03-06",
        bio="Colombian novelist and Nobel Prize laureate, a central figure of magical realism.",
    )
    le_guin = Author.objects.create(
        name="Ursula K. Le Guin",
        born="1929-10-21",
        bio="American author known for her explorations of anarchism, society, and gender in science fiction.",
    )
    morrison = Author.objects.create(
        name="Toni Morrison",
        born="1931-02-18",
        bio="American novelist and Nobel Prize laureate whose works explore African-American identity and history.",
    )

    books = [
        ("Pride and Prejudice", austen, "1813-01-28", "Fiction", "9780141439518"),
        ("Sense and Sensibility", austen, "1811-10-30", "Fiction", "9780141439662"),
        ("1984", orwell, "1949-06-08", "Dystopian", "9780451524935"),
        ("Animal Farm", orwell, "1945-08-17", "Satire", "9780451526342"),
        ("One Hundred Years of Solitude", marquez, "1967-06-05", "Magical Realism", "9780060883287"),
        ("Love in the Time of Cholera", marquez, "1985-01-01", "Romance", "9780307389732"),
        ("The Left Hand of Darkness", le_guin, "1969-03-01", "Science Fiction", "9780441478125"),
        ("A Wizard of Earthsea", le_guin, "1968-11-01", "Fantasy", "9780547722023"),
        ("Beloved", morrison, "1987-09-16", "Historical Fiction", "9781400033416"),
        ("Song of Solomon", morrison, "1977-01-01", "Fiction", "9781400033423"),
    ]
    for book_title, author, year, genre, isbn in books:
        Book.objects.create(title=book_title, author=author, published=year, genre=genre, isbn=isbn)

    print(f"  Seeded {Author.objects.count()} authors, {Book.objects.count()} books")


if __name__ == "__main__":
    from django.core.management import call_command, execute_from_command_line

    call_command("migrate", "--run-syncdb", verbosity=0)
    seed()

    if len(sys.argv) == 1:
        print("Library \u2192 http://localhost:8000")
        execute_from_command_line(["manage", "runserver", "--noreload", "8000"])
    else:
        execute_from_command_line(sys.argv)
