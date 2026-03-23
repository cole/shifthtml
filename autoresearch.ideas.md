# Autoresearch Ideas

## Status: Optimization complete (87+ experiments, 9 sessions)

### Summary
- Sync path: ~1.9% improvement (3.925ms → ~3.85ms), at CPython floor
- Async path: sequential rendering for sync siblings, leaf fast path added
- shifthtml is already ~8% faster than tdom (nearest pure-Python competitor)
- Gap to jinja2/minijinja requires C/Rust extensions

### Tried and Discarded (session 9)
- Sync fallback in async _arender_unbuffered — breaks streaming contract
- Double-run benchmark for noise reduction — selection bias

### Exhausted
All pure-Python optimizations are at the CPython 3.14 floor. The per-operation
budget (~2.5μs across ~1500 operations) cannot be reduced further without
native code or architectural changes to the tree-building API.
