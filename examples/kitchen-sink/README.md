# Kitchen Sink

A comprehensive demo of ShiftHTML rendering every common HTML5 element, served with Python's stdlib `http.server`.

## Run

```
uv run examples/kitchen-sink/app.py
```

Then open http://localhost:8000.

## What's in it

The page covers nearly every HTML5 element and demonstrates several ShiftHTML features:

### Elements

- **Sectioning**: `main`, `section`, `header`, `footer`, `nav`, `article`, `aside`, `hgroup`, `address`
- **Headings**: `h1`–`h6`
- **Text-level**: `em`, `strong`, `small`, `abbr`, `del`, `ins`, `kbd`, `code`, `samp`, `var`, `q`, `sub`, `sup`, `mark`, `cite`
- **Grouping**: `p`, `blockquote`, `pre`, `hr`, `ul`, `ol`, `li`, `dl`, `dt`, `dd`, `figure`, `figcaption`
- **Tables**: `table`, `caption`, `tbody`, `tr`, `th`, `td`
- **Forms**: `form`, `input` (email, number, password, search, tel, text, url, color, date, datetime-local, month, week, time, range, file, radio, checkbox), `select`, `textarea`, `fieldset`, `legend`, `button`
- **Interactive**: `details`, `summary`

### ShiftHTML features

- **`Lazy`** — the fortune quote section uses `Lazy(pick_fortune)` so the random quote is selected at render time, not when the tree is built
- **`defer()`** — the deferred content section renders a placeholder immediately, then swaps in the real content (after a simulated 500ms delay) via an inline `<script>` appended at the end of the response
- **Custom tags** — `hgroup` is defined inline with `TagMeta` since it's not in the built-in tag set
- **Dynamic data** — request count, server timestamp, and stats grid change on every page load
- **Client-side JS** — dark/light theme toggle, served as a static file

### Files

| File | Purpose |
|---|---|
| `app.py` | `http.server` handler — tracks request count, renders page, serves static files |
| `components.py` | All ShiftHTML components for the page |
| `static/style.css` | Page styles |
| `static/theme.js` | Dark/light theme toggle script |
