#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = ["shifthtml"]
#
# [tool.uv.sources]
# shifthtml = { path = ".." }
# ///
"""Benchmark rendering speed on a pre-built tree."""

import argparse
import random
import statistics
import sys
import time

# Re-use the tree builders from the build benchmark.
from bench_build import build_args_tree, build_tree
from benchmark import make_context

from shifthtml import render


def bench(name: str, fn, iterations: int) -> dict:
    # warmup
    for _ in range(10):
        fn()

    times: list[float] = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        result = fn()
        times.append((time.perf_counter() - t0) * 1000)

    stats = {
        "name": name,
        "mean_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
        "min_ms": min(times),
        "output_length": len(result),
    }
    print(
        f"  {name:20s}  "
        f"mean={stats['mean_ms']:8.3f} ms  "
        f"median={stats['median_ms']:8.3f} ms  "
        f"min={stats['min_ms']:8.3f} ms  "
        f"stdev={stats['stdev_ms']:7.3f} ms  "
        f"output={stats['output_length']} chars"
    )
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark shifthtml rendering")
    parser.add_argument("--iterations", type=int, default=200)
    parser.add_argument("--num-products", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    cli = parser.parse_args()

    random.seed(cli.seed)
    ctx = make_context(cli.num_products)

    print(f"Iterations: {cli.iterations}  |  Products: {cli.num_products}  |  Python: {sys.version.split()[0]}")
    print("-" * 90)

    # shifthtml: build once, render many times
    tree = build_tree(ctx)
    bench("shifthtml", lambda: str(tree), cli.iterations)

    # shifthtml-args: template built once, rendered with same data each iteration
    args_tree = build_args_tree()
    bench("shifthtml-args", lambda: render(args_tree, args=ctx), cli.iterations)



if __name__ == "__main__":
    main()
