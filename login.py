
from flask import Flask, render_template, request, redirect, url_for, session,jsonify,flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'avsagd' 
# Database setup
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
conn = sqlite3.connect('tasks.db')
cursor = conn.cursor()


cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        contact_no TEXT
    )
''')


cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        task_name TEXT,
        created_at DATETIME  CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS deleted_tasks (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        task_name TEXT,
        deleted_at DATETIME  CURRENT_TIMESTAMP
    )
''')
cursor.execute('''
    PRAGMA table_info(deleted_tasks)
''')
table_info = cursor.fetchall()
date_column_exists = False
time_column_exists = False
for column in table_info:
    if column[1] == 'deleted_date':
        date_column_exists = True
    elif column[1] == 'deleted_time':
        time_column_exists = True

if not date_column_exists:
    cursor.execute('''
        ALTER TABLE deleted_tasks
        ADD COLUMN deleted_date DATE  CURRENT_DATE
    ''')
if not time_column_exists:
    cursor.execute('''
        ALTER TABLE deleted_tasks
        ADD COLUMN deleted_time TIME  CURRENT_TIME
    ''')
# Retrieve all tasks
cursor.execute('''
    SELECT * FROM tasks
''')
tasks = cursor.fetchall()

# Print all tasks
for task in tasks:
    print(f"ID: {task[0]}, User ID: {task[1]}, Task Name: {task[2]}, Is Completed: {task[3]}")




conn.commit()
conn.close()

@app.route('/')
def login():
    if 'logged_in' in session and session['logged_in']:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['logged_in'] = True
        session['username'] = username
        session['user_id'] = user[0]  
        return redirect(url_for('dashboard'))
    else:
        return 'Invalid credentials'

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_post():
    # Get form data
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']

    # Validate form data
    if not username or not email or not password:
        return 'All fields are required.'

    # Check if username already exists
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    existing_user = cursor.fetchone()
    conn.close()

    if existing_user:
        return 'Username already exists.'

    # Check if email already exists
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
    existing_user = cursor.fetchone()
    conn.close()

    if existing_user:
        return 'Email already exists.'

    

    # Insert user into database
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email,password))
    conn.commit()
    conn.close()

    return redirect(url_for('login'))


@app.route('/add_task', methods=['POST'])
def add_task():
    task_name = request.form['task_name']
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tasks (task_name) VALUES (?)', (task_name,))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks')
    tasks = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', tasks=tasks)

@app.route('/view_tasks')
def view_tasks():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks')
    tasks = cursor.fetchall()
    conn.close()
    return render_template('view_tasks.html', tasks=tasks)
@app.route('/deleted_task/<int:task_id>')
def deleted_task(task_id):
    if 'logged_in' in session and session['logged_in']:
        user_id = session['user_id']
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tasks WHERE id=?', (task_id,))
        task = cursor.fetchone()
        if task:
            if task[2]:  # Check if task[2] is not None or an empty string
                cursor.execute('INSERT INTO deleted_tasks (user_id, task_name, deleted_at) VALUES (?,?,?)', (user_id, task[2], datetime.now()))
                cursor.execute('DELETE FROM tasks WHERE id=?', (task_id,))
                conn.commit()
                conn.close()
                flash('Task deleted successfully')  # Display a success message
                return redirect(url_for('view_deleted_tasks'))
            else:
                flash('Task name cannot be empty')  # Display an error message
                return redirect(url_for('view_deleted_tasks'))
        else:
            return 'Task not found'
    else:
        return redirect(url_for('login'))
@app.route('/view_deleted_tasks')
def view_deleted_tasks():
    if 'logged_in' in session and session['logged_in']:
        user_id = session['user_id']
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM deleted_tasks WHERE user_id=?', (user_id,))
        deleted_tasks = cursor.fetchall()
        conn.close()
        return render_template('view_deleted_tasks.html', deleted_tasks=deleted_tasks)
    else:
        return redirect(url_for('login'))
@app.route('/get_tasks')
def get_tasks():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks')
    tasks = cursor.fetchall()
    conn.close()
    return jsonify([{'task_id': task[0], 'task_name': task[1]} for task in tasks])
@app.route('/profileedit', methods=['GET', 'POST'])
def profile_edit():
    if 'logged_in' in session and session['logged_in']:
        user_id = session['user_id']
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id=?', (user_id,))
        user = cursor.fetchone()
        conn.close()

        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            contact_no = request.form['contact_no']

            # Validate form data
            if not username or not email or not password:
                flash('All fields are required.')
                return render_template('profile_edit.html', user=user)

            # Update user data
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET username=?, email=?, password=?, contact_no=? WHERE id=?',
                           (username, email, password, contact_no, user_id))
            conn.commit()
            conn.close()

            flash('Profile updated successfully')
            return redirect(url_for('dashboard'))

        return render_template('profile_edit.html', user=user)
    else:
        return redirect(url_for('login'))



@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
