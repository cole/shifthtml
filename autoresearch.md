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

### Discarded (no improvement or regression, 42 experiments)
- Fast-path escape (skip html.escape when no special chars) — marginal
- Cache attribute name conversion / fast-path for simple names — regression
- Reorder Node.factory dispatch / type() identity checks — noise/regression
- Pre-compute close tags as ClassVar or instance attr — regression (MRO/init overhead)
- Share empty children list for Text/Comment — regression
- Inline Element.__init__ (skip super) / branch on attrs — consistently regresses
- Single-attr fast path in render_open_tag — regression (next/iter overhead)
- NodeList flattening in Element/Node.render_to_buf — regression (isinstance cost)
- Stack-based iterative renderer — regression (isinstance/issubclass overhead)
- Override render_to_buf on VoidElement — regression (MRO dispatch)
- Remove ABCMeta from TreeNode — no improvement
- Skip append_child validation in Fragment.append — noise
- String concat vs list+join in render_open_tag — noise
- Guard dict.update when no keyword attrs — noise
- Inline _render_attrs / render_open_tag in render_to_buf — noise

### Key Insight
The performance bottleneck is very flat — cost spread across many small operations
(Element.__init__, isinstance, render_open_tag, html.escape, __rshift__, etc).
No single hotspot dominates, making further optimization challenging.
