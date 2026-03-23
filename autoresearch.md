# Autoresearch: shifthtml benchmark runtime

## Objective
Reduce **shifthtml synchronous render time** on the benchmark workload in `bench/benchmark.py` (product listing page).

## Metrics
- **Primary**: `sync_mean_ms` (ms, lower is better)
- **Secondary**: `async_mean_ms`, `sync_median_ms`, `sync_stdev_ms`, `output_length`

## How to Run
`./autoresearch.sh` — outputs `METRIC name=number` lines.

## Files in Scope
- `src/shifthtml/element.py` — core node/element creation and render paths
- `src/shifthtml/render.py` — string + attribute rendering
- `src/shifthtml/tree.py` — tree manipulation helpers
- `src/shifthtml/mappings.py` — attribute helper maps used by elements
- `tests/**` — only if needed to preserve behavior under optimization changes

## Off Limits
- Public benchmark workload semantics in `bench/templates/**`
- Non-performance feature additions unrelated to this benchmark
- Dependency changes

## Constraints
- Preserve output correctness
- `autoresearch.checks.sh` must pass for kept changes
- Keep changes simple and readable

## What's Been Tried
- Baseline harness setup only; no optimizations yet.
- Secondary metric changed to async render mean time to monitor sync/async tradeoffs.
