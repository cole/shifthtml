# bench

Compares **shifthtml** against **jinja2**, **minijinja**, **django templates**, and **tdom** on a
product-listing page with configurable product count.

## Run

```bash
# all engines
uv run bench/benchmark.py

# single engine
uv run bench/benchmark.py --engine shifthtml

# options
uv run bench/benchmark.py --iterations 200 --num-products 100 --output results.json
```
