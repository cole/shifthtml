from shifthtml import div, h1, p, shift, span


def test_text_content_simple():
    f = shift(p >> "hello")
    assert f.root.text_content == "hello"


def test_text_content_nested():
    f = shift(div() >> (p >> "Hello ", p >> (span >> "world")))
    assert f.root.text_content == "Hello world"


def test_text_content_deep():
    f = shift(div >> p >> span >> "deep")
    assert f.root.text_content == "deep"


def test_text_content_empty():
    f = shift(div())
    assert f.root.text_content == ""


def test_text_content_multiple_text_nodes():
    parent = div()
    parent.append_child(shift(h1 >> "Title").root)
    parent.append_child(shift(p >> "Body text").root)
    f = shift(parent)
    assert f.root.text_content == "TitleBody text"


def test_text_content_on_text_node():
    f = shift(span >> "just text")
    text_node = f.root.first_child
    assert text_node.text_content == "just text"
