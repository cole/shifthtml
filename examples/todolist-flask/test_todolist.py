from components import add_todo_form, page, todo_item, todo_list


def make_todo(id: int, title: str, completed: bool = False) -> dict:
    return {"id": id, "title": title, "completed": completed}


def test_page_empty(snapshot):
    assert page([]).render() == snapshot


def test_page_with_todos(snapshot):
    todos = [make_todo(1, "Buy milk"), make_todo(2, "Walk dog", completed=True)]
    assert page(todos).render() == snapshot


def test_todo_item_uncompleted(snapshot):
    assert todo_item(make_todo(1, "Buy milk")).render() == snapshot


def test_todo_item_completed(snapshot):
    assert todo_item(make_todo(2, "Walk dog", completed=True)).render() == snapshot


def test_todo_list_empty(snapshot):
    assert todo_list([]).render() == snapshot


def test_todo_list_multiple(snapshot):
    todos = [make_todo(i, f"Task {i}") for i in range(1, 4)]
    assert todo_list(todos).render() == snapshot


def test_add_todo_form(snapshot):
    assert add_todo_form().render() == snapshot
