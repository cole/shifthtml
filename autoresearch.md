# Autoresearch: shifthtml performance

## Objective
Optimize shifthtml's tree-building and rendering speed. The workload is a product
listing page with 50 product cards, each with nested elements, conditional classes,
dynamic pricing, star ratings, tags, and breadcrumbs. ~37KB HTML output.

## Metrics
- **Primary**: `total_ms` (ms, lower is better) — median build + render time
- **Secondary**: `build_ms` (tree construction), `render_ms` (serialization to string)

## How to Run
`./autoresearch.sh` — outputs `METRIC name=number` lines.

## Files in Scope
- `src/shifthtml/element.py` — Node, Element, Fragment, `>>` operator, `_flatten_into`
- `src/shifthtml/tree.py` — TreeNode base class, parent/child wiring
- `src/shifthtml/render.py` — `render_string`, `render_open_tag`, attribute serialization
- `src/shifthtml/rendering.py` — `render()`, `stream()`, `stream_children()`
- `src/shifthtml/tags.py` — Tag classes via TagMeta
- `src/shifthtml/meta.py` — TagMeta metaclass
- `src/shifthtml/mappings.py` — StyleMap, ClassList, DatasetMap
- `src/shifthtml/types.py` — Type aliases

## Off Limits
- `bench/benchmark.py` — cross-engine comparison benchmark (don't modify)
- `tests/` — don't modify tests; they must keep passing
- Public API — no breaking changes

## Constraints
- All tests must pass (`pytest tests/ -x -q`)
- Type checking must pass (`ty check src/`)
- No new dependencies
- No breaking API changes

## Architecture Notes

### Build path (hot)
`Element.__init__` → allocates dict for attributes, inits `_style`/`_class_list`/`_dataset` to None.
`Node.__rshift__` → creates Fragment, calls `_flatten_into` which loops children,
does isinstance checks, sets parent_node, appends to children list.
`Element.__init__` calls `_convert_attribute_names` → `_snake_to_kebab` for every kwarg.

### Render path (hot)
`render()` → `stream()` → `Element.render_html()` → `render_open_tag()` + `stream_children()`.
`render_open_tag` builds tag string via `_render_attributes` generator.
`stream_children` loops children, dispatches str/Template to `render_string`, nodes to `render_html`.
`render_string` checks `_needs_escape` then calls `html.escape`.

### Key observations
- Every element creation allocates: dict (attributes), list (children), plus `_style`/`_class_list`/`_dataset` slots set to None.
- `_snake_to_kebab` is called for every keyword attribute on every element creation.
- `_flatten_into` does many isinstance checks per child.
- `render_open_tag` joins a list of parts — could potentially use f-strings or pre-built strings.
- `render_string` calls `_needs_escape` (scanning for &, <, >, ", ') then `html.escape` — double work.
- `_render_attributes` is a generator that yields strings — generator overhead per attribute.
- ABCMeta on TreeNode adds metaclass overhead to every subclass instantiation.

## What's Been Tried

### Wins
- **Cache `_convert_attribute_names`** — dict cache avoids repeated `rstrip("_")` + `_snake_to_kebab` (76K calls/build). Small but real.
- **Optimize `Element.__init__`** — skip dict comprehension for common kwargs-only case. Use dict comp directly instead of empty dict + loop.
- **Inline `_render_attributes` into `render_open_tag`** — eliminates generator overhead, and special-cases `isinstance(value, str)` to skip `render_string` generator for plain string attr values.
- **Remove ABCMeta from TreeNode, TagMeta extends `type`** — avoids metaclass overhead on instantiation.

### Dead ends
- **`collect_html` fast path (list-append, no generators)** — zero improvement. Generator `yield from` is well-optimized in CPython 3.14; function call overhead is similar.
- **Inline string handling in `stream_children`** — splitting `isinstance(child, str | Template)` into two checks is slower than the union check.
- **Cache inline imports as module globals** — `global` + `if is None` check per call worse than Python's import cache (`sys.modules` lookup).
- **Pre-compute tag strings via TagMeta (`_open_tag`, `_close_tag`)** — class variable lookup through MRO is slower than f-string formatting. Adding `if attrs:` branch for no-attribute fast path added overhead to the common (has-attrs) path.
- **`str.translate()` instead of `_needs_escape` + `html.escape`** — `translate()` always runs the replacement pass even when nothing needs escaping. The current `_needs_escape` check + conditional `escape()` is faster because most text doesn't need escaping.

### Profiling insights (200 iterations, 50 products)
**Build** (~1.4ms): `__rshift__` 0.183s tottime (46%), `Element.__init__` 0.132s (20%), `_flatten_into` 0.083s (10%), `isinstance` 0.050s (6%).
**Render** (~1.85ms): `Element.render_html` 0.448s (29%), `stream_children` 0.417s (27%), `render_open_tag` 0.226s (15%), `render_string` 0.040s, `_needs_escape` 0.033s, `importlib.parent` 0.032s (inline import overhead).

The generator chain (render_html + stream_children) dominates render at ~56% but alternative dispatch mechanisms don't help because the actual per-call overhead is similar.
