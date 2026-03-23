from unittest.mock import patch

from components import page

from shifthtml import shift


def render(node) -> str:
    with patch("components.sleep"):
        return str(shift(node))


def test_full_page(snapshot):
    assert render(page()) == snapshot
