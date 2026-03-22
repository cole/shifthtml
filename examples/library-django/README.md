# Library

A Django CRUD app for managing books and authors, using ShiftHTML with `StreamingHttpResponse` for all HTML responses.

## Run

```
uv run --script examples/library-django/app.py
```

Then open http://localhost:8000. The database is auto-created and seeded with sample data on first run.

## What's in it

A user-facing admin-style interface with:

- **List views** with search, row actions, and badge counts
- **Detail views** with field grids and related objects (author's books)
- **Create/edit forms** with validation
- **Delete confirmation** pages
- **Active nav state** highlighting the current section
- **Flash messages** after successful actions
- Dark mode via `prefers-color-scheme` (no toggle needed)

### Streaming

Every view returns a `StreamingHttpResponse` wrapping `shift(page).render()`:

```python
def stream(page):
    return StreamingHttpResponse(shift(page).render(), content_type="text/html; charset=utf-8")
```

The generator from `shift().render()` yields HTML chunks as they're built, so the browser can start rendering before the full response is complete.

### Files

| File | Purpose |
|---|---|
| `app.py` | Django settings, migrations, seed data, and entry point |
| `library/models.py` | `Author` and `Book` models |
| `library/urls.py` | URL routes for all CRUD operations |
| `library/views.py` | Views returning `StreamingHttpResponse` |
| `library/components.py` | ShiftHTML components (layout, tables, forms, detail grids) |
| `static/style.css` | Admin-style CSS with `@layer`, `light-dark()`, `oklch` |

### Note

This example skips CSRF middleware for simplicity. A production app should include `CsrfViewMiddleware` and render a hidden `csrfmiddlewaretoken` input in each form.
