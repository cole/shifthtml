from components import add_todo_form, page, todo_item, todo_list

from shifthtml import render


def render_str(node) -> str:
    return "".join(render(node))


def make_todo(id: int, title: str, completed: bool = False) -> dict:
    return {"id": id, "title": title, "completed": completed}


def test_page_empty(snapshot):
    assert render_str(page([])) == snapshot


def test_page_with_todos(snapshot):
    todos = [make_todo(1, "Buy milk"), make_todo(2, "Walk dog", completed=True)]
    assert render_str(page(todos)) == snapshot


def test_todo_item_uncompleted(snapshot):
    assert render_str(todo_item(make_todo(1, "Buy milk"))) == snapshot


def test_todo_item_completed(snapshot):
    assert render_str(todo_item(make_todo(2, "Walk dog", completed=True))) == snapshot


def test_todo_list_empty(snapshot):
    assert render_str(todo_list([])) == snapshot


def test_todo_list_multiple(snapshot):
    todos = [make_todo(i, f"Task {i}") for i in range(1, 4)]
    assert render_str(todo_list(todos)) == snapshot


def test_add_todo_form(snapshot):
    assert render_str(add_todo_form()) == snapshot
