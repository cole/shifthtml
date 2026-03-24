#!/bin/bash
set -euo pipefail
uv run pytest tests/ -x -q 2>&1 | tail -20
uv run ty check src/ 2>&1 | tail -20
