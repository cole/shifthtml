from shifthtml import Element, Fragment


def root(fragment: Fragment) -> Element:
    """Get the root of a fragment as an Element."""
    assert isinstance(fragment.root, Element)
    return fragment.root
