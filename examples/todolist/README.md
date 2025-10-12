# Todo Example

A simple todo list application demonstrating Shift with Flask, HTMX, and SQLite.

## Setup

1. Install dependencies:
```bash
uv pip install -r requirements.txt
```

2. Run the application:
```bash
uv run app.py
```

3. Open your browser to `http://127.0.0.1:5000`

## How it works

The app uses HTMX to make AJAX requests without writing JavaScript:

- `hx-post` adds new todos
- `hx-put` toggles todo completion status
- `hx-delete` removes todos
