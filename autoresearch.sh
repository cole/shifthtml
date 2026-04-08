#!/bin/bash
set -euo pipefail

# Quick syntax check
python -c "import shifthtml" 2>&1 || { echo "METRIC compiled_ms=0"; exit 1; }

# Run benchmark (fixed seed for reproducibility, moderate iterations for speed)
cd "$(dirname "$0")"
RESULT=$(python -c "
import sys, random
sys.path.insert(0, 'bench')
random.seed(42)

from benchmark import make_context, bench_shifthtml, bench_shifthtml_compiled
from bench_build import build_tree

# Compiled benchmark (primary)
c = bench_shifthtml_compiled(80, 50)
print(f'METRIC compiled_ms={c[\"mean_ms\"]:.4f}')

# Direct render benchmark (secondary)
r = bench_shifthtml(80, 50)
print(f'METRIC render_ms={r[\"mean_ms\"]:.4f}')

# Build-only benchmark
ctx = make_context(50)
import time, statistics
times = []
for _ in range(80):
    t0 = time.perf_counter()
    tree = build_tree(ctx)
    str(tree)
    times.append((time.perf_counter() - t0) * 1000)
print(f'METRIC build_ms={statistics.mean(times):.4f}')
")

echo "$RESULT"
