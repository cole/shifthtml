# bench

Compares **shifthtml** against **jinja2**, **minijinja**, and **tdom** on a
product-listing page with configurable product count.

## Setup

```bash
uv add --dev jinja2 minijinja tdom
```

## Run

```bash
# all engines
python bench/benchmark.py

# single engine
python bench/benchmark.py --engine shifthtml

# options
python bench/benchmark.py --iterations 200 --num-products 100 --output results.json
```
