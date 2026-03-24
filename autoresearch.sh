#!/bin/bash
set -euo pipefail

cd bench

# Quick syntax check
uv run python -c "import shifthtml" 2>&1 || { echo "METRIC build_ms=0"; echo "METRIC render_ms=0"; echo "METRIC total_ms=0"; exit 1; }

# Run build benchmark (200 iterations, 50 products, seeded)
BUILD_OUT=$(uv run bench_build.py --iterations 200 --num-products 50 2>&1)
BUILD_MS=$(echo "$BUILD_OUT" | grep 'shifthtml ' | head -1 | grep -oE 'median=[[:space:]]*[0-9.]+' | grep -oE '[0-9.]+')

# Run render benchmark (200 iterations, 50 products, seeded)
RENDER_OUT=$(uv run bench_render.py --iterations 200 --num-products 50 2>&1)
RENDER_MS=$(echo "$RENDER_OUT" | grep 'shifthtml ' | head -1 | grep -oE 'median=[[:space:]]*[0-9.]+' | grep -oE '[0-9.]+')

TOTAL_MS=$(python3 -c "print(round($BUILD_MS + $RENDER_MS, 3))")

echo "$BUILD_OUT"
echo ""
echo "$RENDER_OUT"
echo ""
echo "METRIC build_ms=$BUILD_MS"
echo "METRIC render_ms=$RENDER_MS"
echo "METRIC total_ms=$TOTAL_MS"
