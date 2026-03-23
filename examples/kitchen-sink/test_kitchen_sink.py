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


@freeze_time(FROZEN)
def test_full_page(snapshot):
    random.seed(42)
    assert render(page(request_count=42)) == snapshot


def test_headings(snapshot):
    assert render(headings_section()) == snapshot


def test_nav_and_article(snapshot):
    assert render(nav_and_article_section()) == snapshot


def test_blockquote(snapshot):
    assert render(blockquote_section()) == snapshot


def test_lazy_fortune(snapshot):
    random.seed(42)
    assert render(lazy_fortune_section()) == snapshot


def test_table(snapshot):
    assert render(table_section()) == snapshot


def test_definition_list(snapshot):
    assert render(definition_list_section()) == snapshot


def test_lists(snapshot):
    assert render(lists_section()) == snapshot


def test_address(snapshot):
    assert render(address_section()) == snapshot


def test_pre(snapshot):
    assert render(pre_section()) == snapshot


def test_figure(snapshot):
    assert render(figure_section()) == snapshot


def test_details(snapshot):
    assert render(details_section()) == snapshot


def test_form(snapshot):
    assert render(form_section()) == snapshot
