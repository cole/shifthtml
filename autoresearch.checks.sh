#!/bin/bash
set -euo pipefail

# Tests — only show failures
uv run pytest tests/ -x -q --tb=short 2>&1 | tail -20

# Type checking
uv run ty check src/ 2>&1 | grep -i error || true
