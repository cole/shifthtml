# Autoresearch Ideas

## Promising Optimizations Not Yet Pursued
- **Avoid Fragment allocation in __rshift__**: For the common `element >> "text"` case, return self directly and handle the append_pointer differently. Would save ~87k allocations per iteration.
- **Pre-compute open+close tag for no-attribute elements**: Many elements like `div()`, `span()`, `h1()` etc. are created with no attributes. Cache `"<div>"` and `"</div>"` as class-level strings.
- **Batch _collect for leaf elements**: Elements like `span() >> "text"` could produce `"<span>text</span>"` as a single string instead of 3 separate buf.append() calls.
- **Reduce isinstance calls via type tags**: Add a numeric `_node_type` field to Node subclasses, use int comparison instead of isinstance. Would eliminate ~600k isinstance calls.
- **Cython/mypyc compilation**: The rendering hot loop is pure Python. Compiling it would yield 5-10x improvement.
- **Tuple pooling for children**: Most element children lists are small (1-3 items). Using tuples instead of lists could avoid allocation.
