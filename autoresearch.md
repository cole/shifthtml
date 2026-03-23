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

### Kept (cumulative ~1.6% improvement)
- `render_open_tag` consolidation — single yield for opening tag
- `render_to_buf` fast path — bypasses generators for sync `str()`
- `__slots__` on all node classes — reduces memory and attribute access overhead
- Inline attribute rendering in `render_open_tag` — skip generator for str attrs
- Skip `append_child` validation in `NodeList.__init__` — factory nodes always fresh
- Single-text-child element fast path — combine open+text+close into one `buf.append`

### Discarded (no improvement or regression)
- Fast-path escape (skip html.escape when no special chars) — marginal
- Cache attribute name conversion — marginal
- Reorder Node.factory dispatch — noise
- Pre-compute close tags as ClassVar — regression
- Share empty children list for Text/Comment — regression
- Inline Element.__init__ (skip super) — regression
- Single-attr fast path in render_open_tag — regression
- NodeList flattening in Element.render_to_buf — regression
- Optimize Element.__init__ attribute merging branches — regression
- Stack-based iterative renderer — regression from isinstance/issubclass overhead

### Key Insight
The performance bottleneck is very flat — cost spread across many small operations
(Element.__init__, isinstance, render_open_tag, html.escape, __rshift__, etc).
No single hotspot dominates, making further optimization challenging.
