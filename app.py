import sqlite3
# pyrefly: ignore [missing-import]
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

DATABASE = 'tasks.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                done INTEGER DEFAULT 0,
                category TEXT DEFAULT 'Personal',
                priority TEXT DEFAULT 'Medium',
                due_date TEXT
            )
        ''')
        conn.commit()

init_db()

def task_to_dict(row):
    return {
        'id': row['id'],
        'text': row['text'],
        'done': bool(row['done']),
        'category': row['category'],
        'priority': row['priority'],
        'due_date': row['due_date']
    }

@app.route('/')
def index():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM tasks ORDER BY id DESC')
        rows = cur.fetchall()
        tasks = [task_to_dict(row) for row in rows]
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add_task():
    data = request.json
    text = data.get('text', '').strip()
    category = data.get('category', 'Personal').strip() or 'Personal'
    priority = data.get('priority', 'Medium').strip() or 'Medium'
    due_date = data.get('due_date')
    
    if not due_date or due_date.strip() == '':
        due_date = None
    else:
        due_date = due_date.strip()

    if text:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO tasks (text, done, category, priority, due_date) VALUES (?, 0, ?, ?, ?)',
                (text, category, priority, due_date)
            )
            conn.commit()
            task_id = cur.lastrowid
            cur.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
            row = cur.fetchone()
            return jsonify({'success': True, 'task': task_to_dict(row)})
    return jsonify({'success': False}), 400

@app.route('/update', methods=['POST'])
def update_task():
    data = request.json
    task_id = data.get('id')
    done = 1 if data.get('done') else 0
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('UPDATE tasks SET done = ? WHERE id = ?', (done, task_id))
        conn.commit()
        if cur.rowcount > 0:
            return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Task not found'}), 404

@app.route('/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()
        if cur.rowcount > 0:
            return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Task not found'}), 404

@app.route('/clear', methods=['POST'])
def clear_completed():
    with get_db() as conn:
        conn.execute('DELETE FROM tasks WHERE done = 1')
        conn.commit()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)

