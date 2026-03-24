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
(nothing yet — baseline run)
