# Autoresearch Ideas

## Status: Ceiling Confirmed (78+ experiments, 7 sessions)

Pure-Python optimization is exhausted. Key discovery from session 7:
- `Text.render_to_buf` is called ZERO times in the benchmark — the leaf element 
  fast path in `Element.render_to_buf` handles all text content inline
- The repeated `from shifthtml import ...` inside `_shift_product_card` costs 
  ~0.2ms/iter (~5% of total), but this is benchmark code we cannot change
- Pre-sizing render buffers is slower than append due to CPython's amortized growth

The per-operation budget is ~2.5μs across ~1500 operations. Each operation is
at the CPython C-level floor. No further gains are possible without C extensions
or structural API changes.
