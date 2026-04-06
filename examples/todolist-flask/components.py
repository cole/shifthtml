from shifthtml import body, button, div, form, h1, head, html, input_, link, meta, script, span, title


def page_head():
    return head() >> (
        meta(charset="UTF-8"),
        meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        title() >> "Todo List",
        script(src="https://unpkg.com/htmx.org@1.9.10"),
        link(rel="stylesheet", href="/static/style.css"),
    )


def page(todos):
    return html(lang="en") >> (
        page_head(),
        body()
        >> (
            h1() >> "Todo List",
            add_todo_form(),
            todo_list(todos),
        ),
    )


def add_todo_form():
    text_input = input_(type="text", name="title", placeholder="Add a new todo...", required=True, autocomplete="off")
    submit = button(type="submit") >> "Add"

    return form(class_="add-todo", hx_post="/todos", hx_target="#todo-list", hx_swap="innerHTML") >> (
        text_input,
        submit,
    )


def todo_list(todos):
    if not todos:
        return div(id="todo-list", class_="todo-list empty") >> "No todos yet. Add one above!"

    return div(id="todo-list", class_="todo-list") >> (todo_item(todo) for todo in todos)


def todo_item(todo):
    todo_id = todo["id"]
    is_completed = todo["completed"]

    label_classes = "todo-label completed" if is_completed else "todo-label"

    checkbox = input_(
        type="checkbox",
        hx_put=f"/todos/{todo_id}/toggle",
        hx_target=f"#todo-{todo_id}",
        hx_swap="outerHTML",
        autocomplete="off",
        checked=bool(is_completed),
    )
    label_text = span(class_=label_classes) >> todo["title"]
    delete_btn = (
        button(
            hx_delete=f"/todos/{todo_id}",
            hx_target=f"#todo-{todo_id}",
            hx_swap="outerHTML",
        )
        >> "Delete"
    )

    return div(id=f"todo-{todo_id}", class_="todo-item") >> (checkbox, label_text, delete_btn)
