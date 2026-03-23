from unittest.mock import patch

from components import page

from shifthtml import render


def render_str(node) -> str:
    with patch("components.sleep"):
        return "".join(render(node))


def test_full_page(snapshot):
    assert render_str(page()) == snapshot
