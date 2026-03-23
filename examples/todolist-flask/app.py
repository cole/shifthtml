import sqlite3
from pathlib import Path

from components import page, todo_item, todo_list
from flask import Flask, g, request, send_from_directory

from shifthtml import shift

app = Flask(__name__)
DATABASE = "todos.db"
STATIC_DIR = Path(__file__).parent / "static"


# Database functions
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        db.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed BOOLEAN NOT NULL DEFAULT 0
            )
        """)
        db.commit()


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)


@app.route("/")
def index_route():
    db = get_db()
    todos = db.execute("SELECT * FROM todos ORDER BY id DESC").fetchall()

    return shift(page(todos)).render()


@app.route("/todos", methods=["POST"])
def add_todo():
    title = request.form.get("title")
    db = get_db()
    if title:
        db.execute("INSERT INTO todos (title) VALUES (?)", (title,))
        db.commit()

    todos = db.execute("SELECT * FROM todos ORDER BY id DESC").fetchall()
    return shift(todo_list(todos)).render()


@app.route("/todos/<int:todo_id>/toggle", methods=["PUT"])
def toggle_todo(todo_id):
    db = get_db()
    db.execute("UPDATE todos SET completed = NOT completed WHERE id = ?", (todo_id,))
    db.commit()

    todo = db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    return shift(todo_item(todo)).render()


@app.route("/todos/<int:todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    db = get_db()
    db.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    db.commit()
    return ""


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
