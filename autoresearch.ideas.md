# Autoresearch Ideas

## Exhausted in Pure Python (61+ experiments across 4 sessions)

Key finding: `escape(text, quote=False)` on safe strings (no special chars) is as fast
as a `_needs_escape()` guard check + conditional skip. CPython's `str.replace()` on
strings without the target character is essentially a no-op — it returns the original
string object immediately. This means there's no benefit to guarding `escape()` calls
for text content (quote=False) in the leaf element fast path.

All practical Python-level micro-optimizations have been explored. The bottleneck is
extremely flat (~20 functions each consuming 5-10% of total time).

## Only Viable with Different Approaches
- C extension for render_open_tag + element render_to_buf combo
- Structural API redesign (lazy tree construction, template compilation)
