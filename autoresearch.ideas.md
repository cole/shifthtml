# Autoresearch Ideas

## Status: Ceiling Reached (73 experiments, 5 sessions)

Pure-Python optimization is thoroughly exhausted. All approaches below have been
benchmarked and show no measurable improvement over the current ~3.85ms baseline.

### Definitively Exhausted Angles
- Micro-optimizing render paths (render_open_tag, render_to_buf)
- Reducing isinstance overhead (type() is, hasattr, duck typing)
- Adding branches/fast-paths to Element.__init__
- Caching close tags (ClassVar, instance attr, module dict)
- Inlining functions (_convert_attribute_names, _render_attrs, render_open_tag)
- Reducing object count (NodeList flattening at construction or render time)
- Stack-based iterative renderer
- Pre-escaping text content at construction
- Marker slots on Text for faster leaf detection
- Method overrides on subclasses (MRO dispatch overhead)
- Removing ABCMeta from TreeNode

### Underlying Reason
CPython 3.14 is highly optimized for the patterns shifthtml uses:
- `isinstance` on concrete types: ~50-65ns
- Dict creation/update: ~100ns
- Function call: ~35ns
- f-string: ~20-30ns
- `str.replace` no-op: ~15ns

At ~3.85ms for 900 elements + 600 text nodes + ~860 render calls, the per-operation
budget is ~2.5μs. Each operation is already near the CPython floor.

### Only Viable with Non-Python Approaches
- C extension for render_open_tag + element render_to_buf combo
- Structural API redesign (lazy tree construction, template compilation)
