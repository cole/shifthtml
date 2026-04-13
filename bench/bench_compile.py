#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = ["shifthtml"]
#
# [tool.uv.sources]
# shifthtml = { path = ".." }
# ///
"""Benchmark .compile() vs direct .render() for repeated rendering.

Compares tree-walk rendering against compiled Template iteration on a
fixed-structure page (~50 elements, 5 Slots).
"""

import argparse
import statistics
import sys
import time

from shifthtml import (
    compile,
    div,
    footer,
    h1,
    h2,
    head,
    header,
    html,
    li,
    link,
    meta,
    nav,
    p,
    section,
    slots,
    span,
    style,
    title,
    ul,
)


def build_page():
    """Fixed structure with 5 Slots and 4 iteration (.map) slots."""
    return html(lang="en") >> (
        head()
        >> (
            meta(charset="utf-8"),
            meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            title() >> t"{slots.page_title}",
            link(rel="stylesheet", href="/style.css"),
            style() >> "body { font-family: sans-serif; margin: 0; }",
        ),
        div(class_="wrapper")
        >> (
            header(class_="site-header")
            >> (nav() >> ul() >> slots.nav_items.map(lambda name: li() >> span() >> name),),
            section(class_="hero")
            >> (
                h1() >> t"{slots.heading}",
                p(class_="subtitle") >> t"Hello, {slots.username}!",
            ),
            div(class_="content")
            >> (
                section(class_="main")
                >> (
                    h2() >> "About",
                    p() >> t"{slots.bio}",
                    ul(class_="features") >> slots.features.map(lambda name: li() >> span() >> name),
                ),
                section(class_="sidebar")
                >> (
                    h2() >> "Links",
                    ul() >> slots.sidebar_items.map(lambda name: li() >> span() >> name),
                ),
            ),
            footer(class_="site-footer")
            >> (
                p() >> t"{slots.footer_text}",
                nav() >> ul() >> slots.footer_links.map(lambda name: li() >> span() >> name),
            ),
        ),
    )


RENDER_PARAMS: dict[str, object] = {
    "page_title": "My Page",
    "heading": "Welcome",
    "username": "Alice",
    "bio": "Software engineer and open source contributor.",
    "footer_text": "© 2025 My Site",
    "nav_items": [f"Nav {i}" for i in range(8)],
    "features": [f"Feature {i}" for i in range(10)],
    "sidebar_items": [f"Sidebar item {i}" for i in range(8)],
    "footer_links": [f"Footer link {i}" for i in range(4)],
}


def bench(name: str, fn, iterations: int) -> dict:
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
        f"mean={stats['mean_ms']:8.4f} ms  "
        f"median={stats['median_ms']:8.4f} ms  "
        f"min={stats['min_ms']:8.4f} ms  "
        f"stdev={stats['stdev_ms']:7.4f} ms  "
        f"output={stats['output_length']} chars"
    )
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark .compile() vs .render()")
    parser.add_argument("--iterations", type=int, default=500)
    cli = parser.parse_args()

    page = build_page()
    compiled = compile(page)

    # Verify output parity
    assert page.render(params=RENDER_PARAMS) == compiled.render(params=RENDER_PARAMS), "Output mismatch!"

    print(f"Iterations: {cli.iterations}  |  Python: {sys.version.split()[0]}")
    print(f"Tree: 5 Slots + 4 .map() loops, {len(compiled.render(params=RENDER_PARAMS))} chars output")
    print("-" * 100)

    tree_stats = bench("render(tree)", lambda: page.render(params=RENDER_PARAMS), cli.iterations)
    compiled_stats = bench("render(compiled)", lambda: compiled.render(params=RENDER_PARAMS), cli.iterations)

    print("-" * 100)
    speedup = tree_stats["median_ms"] / compiled_stats["median_ms"]
    print(f"  Speedup: {speedup:.1f}x (median)")


if __name__ == "__main__":
    main()
