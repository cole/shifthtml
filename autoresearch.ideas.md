# Autoresearch Ideas

## Promising Optimizations Not Yet Pursued
- **Cython/mypyc compilation**: The rendering hot loop is pure Python. Compiling it would yield 5-10x improvement.
- **Specialized Element subclasses**: Auto-generate Element._collect variants at class creation time based on void/doctype status, avoiding runtime branch checks.
- **Combine open tag + single text child into one string at build time**: Elements like `span(class_="tag") >> "text"` could eagerly compute `'<span class="tag">text</span>'` during >>, avoiding _collect entirely for leaf nodes.

## Tried and Exhausted
- Fragment allocation avoidance — breaks chaining API
- Pre-compute open tag at init — neutral (init cost offsets render savings)
- Batch _collect leaf f-string — f-string overhead worse than 3 appends
- Type tags — isinstance is already mostly replaced by type() is
- Tuple pooling / empty list avoidance — negligible savings
- Inline _attr_name_cache — slower than try/except function call
