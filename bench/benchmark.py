#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "shifthtml",
#     "jinja2",
#     "minijinja",
#     "tdom",
# ]
#
# [tool.uv.sources]
# shifthtml = { path = ".." }
# ///
"""Benchmark comparing shifthtml, jinja2, minijinja, and tdom."""

import argparse
import json
import random
import statistics
import string
import sys
import time
from pathlib import Path
from typing import Any

TEMPLATE_DIR = Path(__file__).parent / "templates"

# ---------------------------------------------------------------------------
# Shared data generation
# ---------------------------------------------------------------------------


def generate_products(n: int = 50) -> list[dict[str, Any]]:
    categories = [
        ["Electronics", "Computers", "Laptops"],
        ["Clothing", "Men", "Shirts"],
        ["Home & Garden", "Kitchen", "Appliances"],
        ["Sports", "Outdoor", "Camping"],
        ["Books", "Fiction", "Mystery"],
    ]
    products: list[dict[str, Any]] = []
    for i in range(n):
        products.append(
            {
                "name": f"Product {i + 1} - {''.join(random.choices(string.ascii_uppercase, k=3))}",
                "description": (
                    "This is a high-quality product that offers excellent value. "
                    "Features include advanced technology and modern design. "
                    "Perfect for everyday use and special occasions."
                ),
                "price": round(random.uniform(9.99, 999.99), 2),
                "original_price": round(random.uniform(10.00, 1000.00), 2),
                "on_sale": random.choice([True, False]),
                "is_new": random.choice([True, False]),
                "featured": random.choice([True, False]),
                "sku": f"SKU-{i + 1:05d}-{random.randint(1000, 9999)}",
                "stock": random.randint(0, 100),
                "rating": random.randint(1, 5),
                "reviews": random.randint(0, 500),
                "tags": random.sample(
                    ["popular", "bestseller", "eco-friendly", "premium", "limited-edition", "trending"],
                    k=random.randint(1, 4),
                ),
                "category_path": random.choice(categories),
            }
        )
    return products


def make_context(n: int = 50) -> dict[str, Any]:
    return {
        "site_name": "BenchMark Store",
        "font_family": "Arial, sans-serif",
        "bg_color": "#f5f5f5",
        "year": 2025,
        "category": "Featured",
        "nav_items": [
            {"name": "Home", "url": "/"},
            {"name": "Products", "url": "/products"},
            {"name": "About", "url": "/about"},
            {"name": "Contact", "url": "/contact"},
        ],
        "filters": {
            "price_range": "$10 - $100",
            "rating": "4+ stars",
        },
        "products": generate_products(n),
    }


# ---------------------------------------------------------------------------
# Engine: jinja2
# ---------------------------------------------------------------------------


def bench_jinja2(iterations: int, num_products: int) -> dict[str, Any]:
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("products.html")

    # warmup
    ctx = make_context(num_products)
    for _ in range(5):
        template.render(ctx)

    times: list[float] = []
    for _ in range(iterations):
        ctx = make_context(num_products)
        t0 = time.perf_counter()
        result = template.render(ctx)
        times.append((time.perf_counter() - t0) * 1000)

    return _summarise("jinja2", iterations, num_products, times, len(result))


# ---------------------------------------------------------------------------
# Engine: minijinja
# ---------------------------------------------------------------------------


def bench_minijinja(iterations: int, num_products: int) -> dict[str, Any]:
    from minijinja import Environment

    env = Environment()
    env.add_template("base.html", (TEMPLATE_DIR / "base.html").read_text())
    env.add_template("products.html", (TEMPLATE_DIR / "products.html").read_text())

    # warmup
    ctx = make_context(num_products)
    for _ in range(5):
        env.render_template("products.html", **ctx)

    times: list[float] = []
    for _ in range(iterations):
        ctx = make_context(num_products)
        t0 = time.perf_counter()
        result = env.render_template("products.html", **ctx)
        times.append((time.perf_counter() - t0) * 1000)

    return _summarise("minijinja", iterations, num_products, times, len(result))


# ---------------------------------------------------------------------------
# Engine: tdom
# ---------------------------------------------------------------------------


def bench_tdom(iterations: int, num_products: int) -> dict[str, Any]:
    from tdom import html as tdom_html

    def render_page(ctx: dict[str, Any]) -> str:
        products_markup = [_tdom_product_card(tdom_html, p) for p in ctx["products"]]
        nav_links = [tdom_html(t'<a href="{item["url"]}">{item["name"]}</a>') for item in ctx["nav_items"]]
        page = tdom_html(t"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{ctx["site_name"]}</title>
    <style>
        body {{ font-family: {ctx["font_family"]}; background: {ctx["bg_color"]}; }}
    </style>
</head>
<body>
    <header>
        <h1>{ctx["category"]} Products</h1>
        <nav>{nav_links}</nav>
    </header>
    <div class="filters">
        <span>Price: {ctx["filters"]["price_range"]}</span>
        <span>Rating: {ctx["filters"]["rating"]}</span>
    </div>
    <div class="products">{products_markup}</div>
    <footer>&copy; {ctx["year"]} {ctx["site_name"]}</footer>
</body>
</html>""")
        return str(page)

    # warmup
    ctx = make_context(num_products)
    for _ in range(5):
        render_page(ctx)

    times: list[float] = []
    for _ in range(iterations):
        ctx = make_context(num_products)
        t0 = time.perf_counter()
        result = render_page(ctx)
        times.append((time.perf_counter() - t0) * 1000)

    return _summarise("tdom", iterations, num_products, times, len(result))


def _tdom_product_card(tdom_html, p: dict[str, Any]) -> object:  # noqa: ANN001
    classes = "product-card"
    if p["featured"]:
        classes += " featured"
    if p["is_new"]:
        classes += " new"

    if p["on_sale"]:
        pricing = tdom_html(
            t'<span class="original-price">${p["original_price"]:.2f}</span>'
            t'<span class="sale-price">${p["price"]:.2f}</span>'
        )
    else:
        pricing = tdom_html(t'<span class="price">${p["price"]:.2f}</span>')

    stock_cls = "stock" + (" out-of-stock" if p["stock"] == 0 else "")
    stock_text = f"{p['stock']} in stock" if p["stock"] > 0 else "Out of stock"
    stars = "★" * p["rating"] + "☆" * (5 - p["rating"])
    tags = [tdom_html(t'<span class="tag">{tag}</span>') for tag in p["tags"]]
    crumbs = " \u00bb ".join(p["category_path"])

    return tdom_html(t"""<div class="{classes}">
    <div class="product-header">
        <h2>{p["name"]}</h2>
        <span class="sku">{p["sku"]}</span>
    </div>
    <p class="description">{p["description"]}</p>
    <div class="pricing">{pricing}</div>
    <div class="meta">
        <span class="{stock_cls}">{stock_text}</span>
        <span class="rating">{stars}</span>
        <span class="reviews">({p["reviews"]} reviews)</span>
    </div>
    <div class="tags">{tags}</div>
    <nav class="breadcrumb"><span>{crumbs}</span></nav>
</div>""")


# ---------------------------------------------------------------------------
# Engine: shifthtml
# ---------------------------------------------------------------------------


def bench_shifthtml(iterations: int, num_products: int) -> dict[str, Any]:
    from shifthtml import (
        a,
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

    def render_page(ctx: dict[str, Any]) -> str:
        products_markup = [_shift_product_card(ctx_p) for ctx_p in ctx["products"]]
        nav_links = [a(href=item["url"]) >> item["name"] for item in ctx["nav_items"]]

        page = html(lang="en") >> (
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
        return str(page)

    # warmup
    ctx = make_context(num_products)
    for _ in range(5):
        render_page(ctx)

    times: list[float] = []
    for _ in range(iterations):
        ctx = make_context(num_products)
        t0 = time.perf_counter()
        result = render_page(ctx)
        times.append((time.perf_counter() - t0) * 1000)

    return _summarise("shifthtml", iterations, num_products, times, len(result))


# ---------------------------------------------------------------------------
# Engine: shifthtml (async)
# ---------------------------------------------------------------------------


def bench_shifthtml_async(iterations: int, num_products: int) -> dict[str, Any]:
    import asyncio

    from shifthtml import (
        a,
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

    async def render_page(ctx: dict[str, Any]) -> str:
        products_markup = [_shift_product_card(ctx_p) for ctx_p in ctx["products"]]
        nav_links = [a(href=item["url"]) >> item["name"] for item in ctx["nav_items"]]

        page = html(lang="en") >> (
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
        return "".join([chunk async for chunk in page.astream()])

    async def run() -> dict[str, Any]:
        # warmup
        ctx = make_context(num_products)
        for _ in range(5):
            await render_page(ctx)

        times: list[float] = []
        for _ in range(iterations):
            ctx = make_context(num_products)
            t0 = time.perf_counter()
            result = await render_page(ctx)
            times.append((time.perf_counter() - t0) * 1000)

        return _summarise("shifthtml-async", iterations, num_products, times, len(result))

    return asyncio.run(run())


def _shift_product_card(p: dict[str, Any]) -> object:
    from shifthtml import div, h2, nav, p as p_tag, span  # noqa: I001

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
    crumbs = " \u00bb ".join(p["category_path"])

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _summarise(engine: str, iterations: int, num_products: int, times: list[float], output_len: int) -> dict[str, Any]:
    return {
        "engine": engine,
        "iterations": iterations,
        "num_products": num_products,
        "times_ms": times,
        "mean_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
        "min_ms": min(times),
        "max_ms": max(times),
        "output_length": output_len,
    }


def print_results(results: dict[str, Any]) -> None:
    print(
        f"  {results['engine']:16s}  "
        f"mean={results['mean_ms']:8.3f} ms  "
        f"median={results['median_ms']:8.3f} ms  "
        f"min={results['min_ms']:8.3f} ms  "
        f"stdev={results['stdev_ms']:7.3f} ms  "
        f"output={results['output_length']} chars"
    )


# ---------------------------------------------------------------------------
# Engine: shifthtml (compiled shell + dynamic Var content)
# ---------------------------------------------------------------------------


def bench_shifthtml_compiled(iterations: int, num_products: int) -> dict[str, Any]:
    from shifthtml import (
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

    # Build and compile the page shell once — static elements become string
    # ops, Var t-strings become Template ops, and .map() calls become Loop
    # ops that iterate raw data at render time.
    shell = html(lang="en") >> (
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
                h1() >> t"{args.category} Products",
                nav() >> args.nav_items.map(lambda item: a(href=item["url"]) >> item["name"]),
            ),
            div(class_="filters")
            >> (
                span() >> t"Price: {args.price_range}",
                span() >> t"Rating: {args.rating}",
            ),
            div(class_="products") >> args.products.map(_shift_product_card),
            footer() >> t"\u00a9 {args.year} {args.site_name}",
        ),
    )
    compiled = shell.compile()

    def render_page(ctx: dict[str, Any]) -> str:
        return compiled.render(
            args={
                "site_name": ctx["site_name"],
                "font_family": ctx["font_family"],
                "bg_color": ctx["bg_color"],
                "category": ctx["category"],
                "nav_items": ctx["nav_items"],
                "price_range": ctx["filters"]["price_range"],
                "rating": ctx["filters"]["rating"],
                "products": ctx["products"],
                "year": ctx["year"],
            },
        )

    # warmup
    ctx = make_context(num_products)
    for _ in range(5):
        render_page(ctx)

    times: list[float] = []
    for _ in range(iterations):
        ctx = make_context(num_products)
        t0 = time.perf_counter()
        result = render_page(ctx)
        times.append((time.perf_counter() - t0) * 1000)

    return _summarise("shifthtml-compiled", iterations, num_products, times, len(result))


ENGINES = {
    "jinja2": bench_jinja2,
    "minijinja": bench_minijinja,
    "tdom": bench_tdom,
    "shifthtml": bench_shifthtml,
    "shifthtml-compiled": bench_shifthtml_compiled,
    "shifthtml-async": bench_shifthtml_async,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark HTML rendering engines")
    parser.add_argument(
        "--engine",
        choices=[*ENGINES, "all"],
        default="all",
        help="Engine to benchmark (default: all)",
    )
    parser.add_argument("--iterations", type=int, default=100, help="Iterations per engine")
    parser.add_argument("--num-products", type=int, default=50, help="Products to render")
    parser.add_argument("--output", type=Path, help="Write JSON results to file")
    args = parser.parse_args()

    engines = list(ENGINES) if args.engine == "all" else [args.engine]

    print(f"Iterations: {args.iterations}  |  Products: {args.num_products}  |  Python: {sys.version.split()[0]}")
    print("-" * 90)

    all_results: list[dict[str, Any]] = []
    for name in engines:
        try:
            result = ENGINES[name](args.iterations, args.num_products)
            print_results(result)
            all_results.append(result)
        except ImportError as exc:
            print(f"  {name:16s}  SKIPPED ({exc})")
        except Exception as exc:
            print(f"  {name:16s}  ERROR ({exc})")

    if args.output:
        # strip per-iteration times for a compact file
        for r in all_results:
            del r["times_ms"]
        args.output.write_text(json.dumps(all_results, indent=2))
        print(f"\nResults written to {args.output}")


if __name__ == "__main__":
    main()
