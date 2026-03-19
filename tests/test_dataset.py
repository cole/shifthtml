import pytest
from conftest import root

from shifthtml import div, shift


def test_dataset_set():
    el = div()
    f = shift(el)
    root(f).dataset.user_id = "42"
    assert str(f) == '<div data-user-id="42"></div>'


def test_dataset_get():
    el = div(data_user_id="42")
    f = shift(el)
    assert root(f).dataset.user_id == "42"


def test_dataset_get_missing():
    el = div()
    f = shift(el)
    with pytest.raises(AttributeError, match="No data attribute 'data-missing'"):
        _ = root(f).dataset.missing


def test_dataset_delete():
    el = div(data_user_id="42")
    f = shift(el)
    del root(f).dataset.user_id
    assert str(f) == "<div></div>"


def test_dataset_delete_missing():
    el = div()
    f = shift(el)
    with pytest.raises(AttributeError, match="No data attribute"):
        del root(f).dataset.missing


def test_dataset_contains():
    el = div(data_user_id="42")
    f = shift(el)
    assert "user_id" in root(f).dataset
    assert "missing" not in root(f).dataset


def test_dataset_iteration():
    el = div(data_user_id="42", data_role="admin", id="test")
    f = shift(el)
    keys = list(root(f).dataset)
    assert "user_id" in keys
    assert "role" in keys
    assert len(keys) == 2


def test_dataset_overwrites_existing():
    el = div(data_count="1")
    f = shift(el)
    root(f).dataset.count = "2"
    assert root(f).dataset.count == "2"


def test_dataset_stores_lowercase():
    el = div()
    f = shift(el)
    root(f).dataset.User_Name = "cole"
    assert root(f)["data-user-name"] == "cole"
    assert str(f) == '<div data-user-name="cole"></div>'
