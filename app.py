from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import Error

from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"

db_config = {
    'host': "localhost",
    'user': "root",
    'password': "root",
    'database': "task_manager"
}


def get_db_connection():
    return mysql.connector.connect(**db_config)

# Home
@app.route('/')
def home():
    return render_template('index.html')

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                           (username, email, password))
            conn.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for('login'))
        except:
            flash("Username or Email already exists!", "danger")
        finally:
            cursor.close()
            conn.close()

    return render_template('register.html')

# Login
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_input = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user['password'], password_input):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash("Login Successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials!", "danger")

    return render_template('login.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tasks WHERE user_id=%s", (session['user_id'],))
    tasks = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('dashboard.html', tasks=tasks, username=session['username'])

# Profile Page
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get user details
    cursor.execute("SELECT username, email FROM users WHERE id=%s", (session['user_id'],))
    user = cursor.fetchone()

    # Count completed tasks
    cursor.execute("SELECT COUNT(*) AS completed FROM tasks WHERE user_id=%s AND status='Completed'", (session['user_id'],))
    completed = cursor.fetchone()['completed']

    # Count all tasks
    cursor.execute("SELECT COUNT(*) AS total FROM tasks WHERE user_id=%s", (session['user_id'],))
    total = cursor.fetchone()['total']

    cursor.close()
    conn.close()

    return render_template("profile.html", user=user, completed=completed, total=total)


# Add Task
@app.route('/add_task', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    title = request.form['title']
    description = request.form['description']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (user_id, title, description) VALUES (%s,%s,%s)",
                   (session['user_id'], title, description))
    conn.commit()
    cursor.close()
    conn.close()

    flash("Task added successfully!", "success")
    return redirect(url_for('dashboard'))

# Update Task Status
@app.route('/update_task/<int:task_id>/<string:status>')
def update_task(task_id, status):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status=%s WHERE id=%s AND user_id=%s",
                   (status, task_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()

    flash("Task status updated!", "info")
    return redirect(url_for('dashboard'))

# Delete Task
@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id=%s AND user_id=%s", (task_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()

    flash("Task deleted!", "danger")
    return redirect(url_for('dashboard'))


# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash("You have logged out.", "info")
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
