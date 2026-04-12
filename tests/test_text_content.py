from shifthtml import div, h1, p, span


def test_text_content_simple():
    f = p() >> "hello"
    assert f.text_content == "hello"


def test_text_content_nested():
    f = div() >> (p() >> "Hello ", p() >> (span() >> "world"))
    assert f.text_content == "Hello world"


def test_text_content_deep():
    f = div() >> p() >> span() >> "deep"
    assert f.text_content == "deep"


def test_text_content_empty():
    el = div()
    assert el.text_content == ""


def test_text_content_multiple_text_nodes():
    parent = div()
    parent.append_child(h1() >> "Title")
    parent.append_child(p() >> "Body text")
    assert parent.text_content == "TitleBody text"


def test_string_child_is_first_class():
    f = span() >> "just text"
    assert f.first_child == "just text"
    assert f.text_content == "just text"
