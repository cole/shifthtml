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

FROZEN = "2025-06-15 12:00:00"


@freeze_time(FROZEN)
def test_full_page(snapshot):
    random.seed(42)
    assert page(request_count=42).render() == snapshot


def test_headings(snapshot):
    assert headings_section().render() == snapshot


def test_nav_and_article(snapshot):
    assert nav_and_article_section().render() == snapshot


def test_blockquote(snapshot):
    assert blockquote_section().render() == snapshot


def test_lazy_fortune(snapshot):
    random.seed(42)
    assert lazy_fortune_section().render() == snapshot


def test_table(snapshot):
    assert table_section().render() == snapshot


def test_definition_list(snapshot):
    assert definition_list_section().render() == snapshot


def test_lists(snapshot):
    assert lists_section().render() == snapshot


def test_address(snapshot):
    assert address_section().render() == snapshot


def test_pre(snapshot):
    assert pre_section().render() == snapshot


def test_figure(snapshot):
    assert figure_section().render() == snapshot


def test_details(snapshot):
    assert details_section().render() == snapshot


def test_form(snapshot):
    assert form_section().render() == snapshot
