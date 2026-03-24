#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = ["shifthtml"]
#
# [tool.uv.sources]
# shifthtml = { path = ".." }
# ///
"""Benchmark tree-building speed (element creation + >> wiring)."""

import argparse
import random
import statistics
import sys
import time

from benchmark import make_context

from shifthtml import (
    Lazy,
    a,
    args,
    body,
    div,
    footer,
    h1,
    head,
    header,
    html,
    meta,
    nav,
    span,
    style,
    title,
)


def _product_card(p: dict) -> object:
    from shifthtml import div, h2, nav, span
    from shifthtml import p as p_tag

    classes = "product-card"
    if p["featured"]:
        classes += " featured"
    if p["is_new"]:
        classes += " new"

    if p["on_sale"]:
        pricing = (
            span(class_="original-price") >> f"${p['original_price']:.2f}",
            span(class_="sale-price") >> f"${p['price']:.2f}",
        )
    else:
        pricing = (span(class_="price") >> f"${p['price']:.2f}",)

    stock_cls = "stock" + (" out-of-stock" if p["stock"] == 0 else "")
    stock_text = f"{p['stock']} in stock" if p["stock"] > 0 else "Out of stock"
    stars = "★" * p["rating"] + "☆" * (5 - p["rating"])
    tags = [span(class_="tag") >> tag for tag in p["tags"]]
    crumbs = " » ".join(p["category_path"])

    return div(class_=classes) >> (
        div(class_="product-header")
        >> (
            h2() >> p["name"],
            span(class_="sku") >> p["sku"],
        ),
        p_tag(class_="description") >> p["description"],
        div(class_="pricing") >> pricing,
        div(class_="meta")
        >> (
            span(class_=stock_cls) >> stock_text,
            span(class_="rating") >> stars,
            span(class_="reviews") >> f"({p['reviews']} reviews)",
        ),
        div(class_="tags") >> tags,
        nav(class_="breadcrumb") >> (span() >> crumbs),
    )


def build_tree(ctx: dict) -> object:
    products_markup = [_product_card(p) for p in ctx["products"]]
    nav_links = [a(href=item["url"]) >> item["name"] for item in ctx["nav_items"]]

    return html(lang="en") >> (
        head()
        >> (
            meta(charset="UTF-8"),
            meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            title() >> ctx["site_name"],
            style() >> f"body {{ font-family: {ctx['font_family']}; background: {ctx['bg_color']}; }}",
        ),
        body()
        >> (
            header()
            >> (
                h1() >> f"{ctx['category']} Products",
                nav() >> nav_links,
            ),
            div(class_="filters")
            >> (
                span() >> f"Price: {ctx['filters']['price_range']}",
                span() >> f"Rating: {ctx['filters']['rating']}",
            ),
            div(class_="products") >> products_markup,
            footer() >> f"© {ctx['year']} {ctx['site_name']}",
        ),
    )


def build_args_tree() -> object:
    return html(lang="en") >> (
        head()
        >> (
            meta(charset="UTF-8"),
            meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            title() >> t"{args.site_name}",
            style() >> t"body {{ font-family: {args.font_family}; background: {args.bg_color}; }}",
        ),
        body()
        >> (
            header()
            >> (
                Lazy(lambda: h1() >> f"{args.category()} Products"),
                Lazy(lambda: nav() >> [a(href=item["url"]) >> item["name"] for item in args.nav_items()]),
            ),
            div(class_="filters")
            >> Lazy(
                lambda: (
                    span() >> f"Price: {args.filters()['price_range']}",
                    span() >> f"Rating: {args.filters()['rating']}",
                )
            ),
            div(class_="products") >> Lazy(lambda: [_product_card(p) for p in args.products()]),
            Lazy(lambda: footer() >> f"© {args.year()} {args.site_name()}"),
        ),
    )


def bench(name: str, fn, iterations: int) -> dict:
    # warmup
    for _ in range(10):
        fn()

    times: list[float] = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        fn()
        times.append((time.perf_counter() - t0) * 1000)

    result = {
        "name": name,
        "mean_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
        "min_ms": min(times),
    }
    print(
        f"  {name:20s}  "
        f"mean={result['mean_ms']:8.3f} ms  "
        f"median={result['median_ms']:8.3f} ms  "
        f"min={result['min_ms']:8.3f} ms  "
        f"stdev={result['stdev_ms']:7.3f} ms"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark shifthtml tree building")
    parser.add_argument("--iterations", type=int, default=200)
    parser.add_argument("--num-products", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    cli = parser.parse_args()

    random.seed(cli.seed)
    ctx = make_context(cli.num_products)

    print(f"Iterations: {cli.iterations}  |  Products: {cli.num_products}  |  Python: {sys.version.split()[0]}")
    print("-" * 90)

    bench("shifthtml", lambda: build_tree(ctx), cli.iterations)
    bench("shifthtml-args", lambda: build_args_tree(), cli.iterations)


if __name__ == "__main__":
    main()
