from components import page

from shifthtml import render


def test_full_page(snapshot):
    assert render(page()) == snapshot
