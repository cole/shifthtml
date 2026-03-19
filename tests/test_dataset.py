import pytest

from shifthtml import div, shift


def test_dataset_set():
    el = div()
    f = shift(el)
    f.root.dataset.user_id = "42"
    assert str(f) == '<div data-user-id="42"></div>'


def test_dataset_get():
    el = div(data_user_id="42")
    f = shift(el)
    assert f.root.dataset.user_id == "42"


def test_dataset_get_missing():
    el = div()
    f = shift(el)
    with pytest.raises(AttributeError, match="No data attribute 'data-missing'"):
        _ = f.root.dataset.missing


def test_dataset_delete():
    el = div(data_user_id="42")
    f = shift(el)
    del f.root.dataset.user_id
    assert str(f) == "<div></div>"


def test_dataset_delete_missing():
    el = div()
    f = shift(el)
    with pytest.raises(AttributeError, match="No data attribute"):
        del f.root.dataset.missing


def test_dataset_contains():
    el = div(data_user_id="42")
    f = shift(el)
    assert "user_id" in f.root.dataset
    assert "missing" not in f.root.dataset


def test_dataset_iteration():
    el = div(data_user_id="42", data_role="admin", id="test")
    f = shift(el)
    keys = list(f.root.dataset)
    assert "user_id" in keys
    assert "role" in keys
    assert len(keys) == 2


def test_dataset_overwrites_existing():
    el = div(data_count="1")
    f = shift(el)
    f.root.dataset.count = "2"
    assert f.root.dataset.count == "2"


def test_dataset_stores_lowercase():
    el = div()
    f = shift(el)
    f.root.dataset.User_Name = "cole"
    assert f.root.get_attribute("data-user-name") == "cole"
    assert str(f) == '<div data-user-name="cole"></div>'
