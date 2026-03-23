#!/bin/bash
set -euo pipefail

uv run ruff check .
uv run ty check src/
uv run pytest -q
