import pytest

from shifthtml import div


def test_dataset_set():
    el = div()
    el.dataset.user_id = "42"
    assert str(el) == '<div data-user-id="42"></div>'


def test_dataset_get():
    el = div(data_user_id="42")
    assert el.dataset.user_id == "42"


def test_dataset_get_missing():
    el = div()
    with pytest.raises(AttributeError, match="No data attribute 'data-missing'"):
        _ = el.dataset.missing


def test_dataset_delete():
    el = div(data_user_id="42")
    del el.dataset.user_id
    assert str(el) == "<div></div>"


def test_dataset_delete_missing():
    el = div()
    with pytest.raises(AttributeError, match="No data attribute"):
        del el.dataset.missing


def test_dataset_contains():
    el = div(data_user_id="42")
    assert "user_id" in el.dataset
    assert "missing" not in el.dataset


def test_dataset_iteration():
    el = div(data_user_id="42", data_role="admin", id="test")
    keys = list(el.dataset)
    assert "user_id" in keys
    assert "role" in keys
    assert len(keys) == 2


def test_dataset_overwrites_existing():
    el = div(data_count="1")
    el.dataset.count = "2"
    assert el.dataset.count == "2"


def test_dataset_repr():
    el = div(data_user_id="42")
    assert "user_id" in repr(el.dataset)
    assert "42" in repr(el.dataset)


def test_dataset_stores_lowercase():
    el = div()
    el.dataset.User_Name = "cole"
    assert el["data-user-name"] == "cole"
    assert str(el) == '<div data-user-name="cole"></div>'
