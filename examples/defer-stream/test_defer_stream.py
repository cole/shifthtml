import random
from unittest.mock import patch

from components import page


def test_full_page(snapshot):
    random.seed(42)
    with patch("components.sleep"):
        assert page().render() == snapshot
