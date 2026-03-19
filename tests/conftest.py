import pytest

from shifthtml import Element, Fragment
from shifthtml.plugin import _registry


@pytest.fixture(autouse=True)
def _clean_plugin_registry():
    _registry.clear()
    yield
    _registry.clear()


def root(fragment: Fragment) -> Element:
    """Get the root of a fragment as an Element."""
    assert isinstance(fragment.root, Element)
    return fragment.root
