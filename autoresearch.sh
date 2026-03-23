#!/bin/bash
set -euo pipefail

# Fast pre-check
python -m py_compile src/shifthtml/*.py

SYNC_JSON="$(mktemp)"
ASYNC_JSON="$(mktemp)"
trap 'rm -f "$SYNC_JSON" "$ASYNC_JSON"' EXIT

uv run bench/benchmark.py \
  --engine shifthtml \
  --iterations 80 \
  --num-products 50 \
  --output "$SYNC_JSON" >/dev/null

uv run bench/benchmark.py \
  --engine shifthtml-async \
  --iterations 80 \
  --num-products 50 \
  --output "$ASYNC_JSON" >/dev/null

python - <<'PY' "$SYNC_JSON" "$ASYNC_JSON"
from __future__ import annotations

import json
import sys

sync_rows = json.loads(open(sys.argv[1]).read())
async_rows = json.loads(open(sys.argv[2]).read())

if not sync_rows or not async_rows:
    raise SystemExit("benchmark output missing")

sync = sync_rows[0]
async_ = async_rows[0]

print(f"METRIC sync_mean_ms={sync['mean_ms']:.6f}")
print(f"METRIC async_mean_ms={async_['mean_ms']:.6f}")
print(f"METRIC sync_median_ms={sync['median_ms']:.6f}")
print(f"METRIC sync_stdev_ms={sync['stdev_ms']:.6f}")
print(f"METRIC output_length={float(sync['output_length']):.1f}")
PY
