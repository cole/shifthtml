# Datastar + Sanic Example

A real-time clock demonstrating Shift usage with Sanic and Datastar.

## Setup

1. Run the application: `uv run app.py`
2. Open your browser to `http://127.0.0.1:8000`

## How it works

The app uses Datastar to stream the current time via Server-Sent Events:

- **Element patching**: the server morphs a `<div>` with the updated time each second
- **Signal patching**: the server updates a `currentTime` signal, and Datastar's `data-text` binding keeps the display in sync

ShiftHTML components generate all HTML — both the initial page and the SSE fragments. Datastar attributes are produced by `datastar-py`'s `attribute_generator` and passed as dicts to ShiftHTML elements.
