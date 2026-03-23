# bench

Compares **shifthtml** against **jinja2**, **minijinja**, and **tdom** on a
product-listing page with configurable product count.

## Setup

```bash
cd bench
uv sync
```

## Run

```bash
# all engines
uv run python benchmark.py

# single engine
uv run python benchmark.py --engine shifthtml

# options
uv run python benchmark.py --iterations 200 --num-products 100 --output results.json
```
