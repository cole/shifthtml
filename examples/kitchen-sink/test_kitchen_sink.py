import random

from components import (
    address_section,
    blockquote_section,
    definition_list_section,
    details_section,
    figure_section,
    form_section,
    headings_section,
    lazy_fortune_section,
    lists_section,
    nav_and_article_section,
    page,
    pre_section,
    table_section,
)
from freezegun import freeze_time

from shifthtml import render

FROZEN = "2025-06-15 12:00:00"


def render_str(node) -> str:
    return "".join(render(node))


@freeze_time(FROZEN)
def test_full_page(snapshot):
    random.seed(42)
    assert render_str(page(request_count=42)) == snapshot


def test_headings(snapshot):
    assert render_str(headings_section()) == snapshot


def test_nav_and_article(snapshot):
    assert render_str(nav_and_article_section()) == snapshot


def test_blockquote(snapshot):
    assert render_str(blockquote_section()) == snapshot


def test_lazy_fortune(snapshot):
    random.seed(42)
    assert render_str(lazy_fortune_section()) == snapshot


def test_table(snapshot):
    assert render_str(table_section()) == snapshot


def test_definition_list(snapshot):
    assert render_str(definition_list_section()) == snapshot


def test_lists(snapshot):
    assert render_str(lists_section()) == snapshot


def test_address(snapshot):
    assert render_str(address_section()) == snapshot


def test_pre(snapshot):
    assert render_str(pre_section()) == snapshot


def test_figure(snapshot):
    assert render_str(figure_section()) == snapshot


def test_details(snapshot):
    assert render_str(details_section()) == snapshot


def test_form(snapshot):
    assert render_str(form_section()) == snapshot
