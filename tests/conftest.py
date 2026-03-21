import pytest

from shifthtml import Element, Fragment, clear_registry


@pytest.fixture(autouse=True)
def _clean_plugin_registry():
    clear_registry()
    yield
    clear_registry()


def root(fragment: Fragment) -> Element:
    """Get the root of a fragment as an Element."""
    assert isinstance(fragment.root, Element)
    return fragment.root
