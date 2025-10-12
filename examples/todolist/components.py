from shifthtml import body, button, div, form, h1, head, html, input_, meta, script, span, style, title

CSS = """body {
  font-family: system-ui, -apple-system, sans-serif;
  max-width: 600px;
  margin: 40px auto;
  padding: 0 20px;
  background: #f5f5f5;
}
h1 {
  color: #333;
  text-align: center;
}
.add-todo {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}
.add-todo input {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}
.add-todo button {
  padding: 12px 24px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}
.add-todo button:hover {
  background: #0056b3;
}

.todo-list {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
.todo-list.empty {
  padding: 20px;
  text-align: center;
  color: #999;
}

.todo-item {
  padding: 16px;
  border-bottom: 1px solid #eee;
  display: flex;
  align-items: center;
  gap: 12px;
}

.todo-item button {
  margin-left: auto;
  background: transparent;
  border: none;
  color: #ff4d4f;
  cursor: pointer;
}

.todo-item input {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.todo-label {
  flex: 1;
}

.todo-label.completed {
  text-decoration: line-through;
  color: #999;
}
"""


def page_header():
    return head >> (
        meta({"charset": "UTF-8"}),
        meta({"name": "viewport", "content": "width=device-width, initial-scale=1.0"}),
        title >> "Todo List",
        script({"src": "https://unpkg.com/htmx.org@1.9.10"}),
        style >> CSS,
    )


def page(todos):
    return html({"lang": "en"}) >> (
        page_header(),
        body
        >> (
            h1 >> "Todo List",
            add_todo_form,
            todo_list(todos),
        ),
    )


def add_todo_form():
    return (
        form(classname="add-todo", hx_post="/todos", hx_target="#todo-list", hx_swap="innerHTML")
        >> (
            input_(type="text", name="title", placeholder="Add a new todo...", required=True, autocomplete="off"),
            button(type="submit") >> "Add",
        ),
    )


def todo_list(todos):
    if not todos:
        return div(classname="todo-list empty") >> "No todos yet. Add one above!"

    return div(id="todo-list", classname="todo-list") >> (todo_item(todo) for todo in todos)


def todo_item(todo):
    todo_id = todo["id"]
    is_completed = todo["completed"]

    label_classes = set(["todo-label"])
    if is_completed:
        label_classes.add("completed")

    checkbox_attrs = {
        "type": "checkbox",
        "hx-put": f"/todos/{todo_id}/toggle",
        "hx-target": f"#todo-{todo_id}",
        "hx-swap": "outerHTML",
        "autocomplete": "off",
    }
    if is_completed:
        checkbox_attrs["checked"] = "checked"

    return div(id=f"todo-{todo_id}", classname="todo-item") >> (
            input_(checkbox_attrs),
            span(classname=label_classes) >> todo["title"],
            button(
                hx_delete=f"/todos/{todo_id}",
                hx_target=f"#todo-{todo_id}",
                hx_swap="outerHTML",
            )
            >> "Delete",
        )
  
