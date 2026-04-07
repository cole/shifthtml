# Autoresearch: Optimize shifthtml Rendering Performance

## Objective
Optimize the shifthtml library's rendering speed — the time to build a tree of elements and render them to an HTML string. The benchmark builds a realistic product listing page (50 products, navigation, filters) and measures the full build+render cycle.

## Metrics
- **Primary**: `render_ms` (ms, lower is better) — mean time for shifthtml engine in benchmark.py
- **Secondary**: `compiled_ms` — mean time for shifthtml-compiled engine, `build_ms` — tree building time

## How to Run
`./autoresearch.sh` — outputs `METRIC name=number` lines.

## Files in Scope
- `src/shifthtml/rendering.py` — Core rendering: stream_children, render_string, render_open_tag, _render_node
- `src/shifthtml/element.py` — Element, Fragment, __rshift__, _flatten_into, _stream
- `src/shifthtml/tree.py` — Node base class, render/stream methods
- `src/shifthtml/operations.py` — Compiled template IR and execution (_exec_ops, _stream_ops)
- `src/shifthtml/compile.py` — Template compilation
- `src/shifthtml/types.py` — Type guards, protocols
- `src/shifthtml/mappings.py` — ClassList, StyleMap, DatasetMap

## Off Limits
- `bench/` — benchmark files (except autoresearch scripts)
- Test files
- Public API signatures (render, stream, astream)
- Plugin system interface

## Constraints
- All existing tests must pass (`uv run pytest tests/ -x -q`)
- Type checking must pass (`uv run ty check src/`)
- No changes to public API contracts
- Correctness: rendered output must remain identical

## What's Been Tried
*Nothing yet — establishing baseline.*

## Hot Path Analysis (from profiling)
1. `_render_node` + `stream_children` — deepest call stack, most cumulative time
2. `Element._stream` — called per-element, renders open/close tags + children
3. `__rshift__` — tree building operator, called per element
4. `render_open_tag` — attribute serialization
5. `_flatten_into` — child list normalization
6. `isinstance` — ~600k calls in 100 iterations, type dispatch overhead
7. `render_string` — text/template content rendering
8. `_needs_escape` — HTML escape check on every string
