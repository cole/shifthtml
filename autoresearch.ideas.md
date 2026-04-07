# Autoresearch Ideas

## Promising Optimizations Not Yet Pursued
- **Cython/mypyc compilation**: The rendering hot loop is pure Python. Compiling _collect + _collect_children + _flatten_into would yield 3-5x improvement.
- **Pre-render leaf elements at build time**: `span(class_="tag") >> "text"` could store `'<span class="tag">text</span>'` directly, skipping _collect for 74% of elements. Needs immutability contract.

## Tried and Exhausted
- Fragment allocation avoidance — breaks chaining API
- Pre-compute open tag at init — neutral (init cost offsets render savings)
- Batch _collect leaf f-string — f-string overhead worse than 3 appends
- Type tags — isinstance is already mostly replaced by type() is
- Tuple pooling / empty list avoidance — negligible savings
- Inline _attr_name_cache — slower than try/except function call
