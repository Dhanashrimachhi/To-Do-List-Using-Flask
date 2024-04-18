from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__, static_url_path='/static')
app.secret_key = '123456'


conn = sqlite3.connect('task_manager.db', check_same_thread=False)
cursor = conn.cursor()


cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        contact TEXT NOT NULL,
        email TEXT NOT NULL,
        password TEXT NOT NULL,
        photo TEXT
    )
''')
conn.commit()


cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        task TEXT NOT NULL,
        timestamp DATETIME NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')
conn.commit()


cursor.execute('''
    CREATE TABLE IF NOT EXISTS completed_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        task TEXT NOT NULL,
        completion_time DATETIME NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')
conn.commit()

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('profile'))
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user[0]
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid email or password')

    return render_template('login.html', error=None)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        contact = request.form.get('contact')
        email = request.form.get('email')
        password = request.form.get('password')
        photo = request.form.get('photo')

        cursor.execute('INSERT INTO users (full_name, contact, email, password, photo) VALUES (?, ?, ?, ?, ?)',
                       (full_name, contact, email, password, photo))
        conn.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/index')
def index():
    return render_template('dashboard.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']


    cursor.execute('SELECT * FROM tasks WHERE user_id = ? ORDER BY timestamp DESC', (user_id,))
    tasks = [{'id': row[0], 'task': row[2], 'timestamp': row[3]} for row in cursor.fetchall()]

    return render_template('dashboard.html', tasks=tasks)

@app.route('/add_task', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    task = request.form.get('task')
    timestamp = datetime.now()


    cursor.execute('INSERT INTO tasks (user_id, task, timestamp) VALUES (?, ?, ?)', (user_id, task, timestamp))
    conn.commit()

    return redirect(url_for('dashboard'))

@app.route('/complete_task', methods=['POST'])
def complete_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    task_id = int(request.form.get('task_id'))


    cursor.execute('SELECT * FROM tasks WHERE id = ? AND user_id = ?', (task_id, user_id))
    task = cursor.fetchone()

    if task:
        # Move task to completed_tasks table
        cursor.execute('INSERT INTO completed_tasks (user_id, task, completion_time) VALUES (?, ?, ?)',
                       (user_id, task[2], datetime.now()))
        conn.commit()


        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()

    return redirect(url_for('dashboard'))

@app.route('/remove_completed_task', methods=['POST'])
def remove_completed_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    task_id = int(request.form.get('task_id'))


    cursor.execute('DELETE FROM completed_tasks WHERE id = ? AND user_id = ?', (task_id, user_id))
    conn.commit()

    return redirect(url_for('history'))


@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']


    cursor.execute('SELECT * FROM completed_tasks WHERE user_id = ? ORDER BY completion_time DESC', (user_id,))
    completed_tasks = [{'id': row[0], 'task': row[2], 'completion_time': datetime.strptime(row[3], '%Y-%m-%d %H:%M:%S.%f')} for row in cursor.fetchall()]

    return render_template('history.html', completed_tasks=completed_tasks)



@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        contact = request.form.get('contact')
        email = request.form.get('email')
        password = request.form.get('password')
        photo = request.form.get('photo')


        cursor.execute('UPDATE users SET full_name = ?, contact = ?, email = ?, password = ?, photo = ? WHERE id = ?',
                       (full_name, contact, email, password, photo, user_id))
        conn.commit()

        return redirect(url_for('profile'))


    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    return render_template('profile.html', user=user)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    # return redirect(url_for('login'))
    # if 'user_id' not in session:
    #     return redirect(url_for('login'))

    return render_template('logout.html')



if __name__ == '__main__':
    app.run(debug=True)