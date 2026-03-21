# Chat with Datastar

A real-time multi-tab chat client built with ShiftHTML, Litestar, and Datastar.

## Setup

1. Run the application: `uv run app.py`
2. Open your browser to `http://127.0.0.1:8000`

The landing page shows two chat clients side by side in iframes. Each gets a unique username. Open additional tabs to add more participants.

## How it works

- **Async rendering**: The initial page uses `arender()` to resolve an async component that loads the message history
- **Real-time updates**: A long-lived SSE connection (`/feed`) polls for new messages and streams them to all connected clients via `patch_elements`
- **Form submit**: Enter key and button click both submit via a `<form>` with Datastar's `data-on:submit.prevent`

ShiftHTML components generate all HTML. Datastar attributes are produced by `datastar-py`'s `attribute_generator`.
