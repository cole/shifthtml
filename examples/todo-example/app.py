import sqlite3
from flask import Flask, render_template, request, g

app = Flask(__name__)
DATABASE = 'todos.db'

# Database functions
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed BOOLEAN NOT NULL DEFAULT 0
            )
        ''')
        db.commit()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/todos')
def get_todos():
    db = get_db()
    todos = db.execute('SELECT * FROM todos ORDER BY id DESC').fetchall()
    return render_template('todos.html', todos=todos)

@app.route('/todos', methods=['POST'])
def add_todo():
    title = request.form.get('title')
    if title:
        db = get_db()
        db.execute('INSERT INTO todos (title) VALUES (?)', (title,))
        db.commit()

    todos = db.execute('SELECT * FROM todos ORDER BY id DESC').fetchall()
    return render_template('todos.html', todos=todos)

@app.route('/todos/<int:todo_id>/toggle', methods=['PUT'])
def toggle_todo(todo_id):
    db = get_db()
    db.execute('UPDATE todos SET completed = NOT completed WHERE id = ?', (todo_id,))
    db.commit()

    todo = db.execute('SELECT * FROM todos WHERE id = ?', (todo_id,)).fetchone()
    return render_template('todo_item.html', todo=todo)

@app.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    db = get_db()
    db.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
    db.commit()
    return ''

if __name__ == '__main__':
    init_db()
    app.run(debug=True)