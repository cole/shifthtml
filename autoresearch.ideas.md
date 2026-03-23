# Autoresearch Ideas

## Status: Ceiling Reached (67 experiments, 4 sessions)

Pure-Python micro-optimization is exhausted. The benchmark spends 74% on tree
construction (object creation, dict ops, append_child) and 26% on rendering
(render_open_tag, escape, buf.append). Both paths are dominated by CPython
C-level builtins that can't be beaten at the Python level.

Key measurement challenge: ±10% variance (±0.4ms on 3.85ms) makes improvements
below ~0.1ms undetectable.

## Only Viable with Different Approaches
- C extension for render_open_tag + element render_to_buf combo
- Structural API redesign (lazy tree construction, template compilation)
