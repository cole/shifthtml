from components import page


def test_full_page(snapshot):
    assert page().render() == snapshot
