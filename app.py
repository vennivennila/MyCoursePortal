from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize database with the is_admin column
def init_db():
    conn = sqlite3.connect('courses.db')
    cursor = conn.cursor()
    
    # Create users table with is_admin column
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            email TEXT,
            is_admin INTEGER DEFAULT 0  -- Add is_admin column (default to 0)
        )
    ''')
    
    # Create courses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            details TEXT,
            materials TEXT
        )
    ''')

    # Create enrollments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS enrollments (
            user_id INTEGER,
            course_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (course_id) REFERENCES courses (id)
        )
    ''')

    # Add an admin user if no users exist
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:  # No users exist, so create an admin user
        cursor.execute('''
            INSERT INTO users (username, password, email, is_admin)
            VALUES (?, ?, ?, ?)
        ''', ('admin', generate_password_hash('adminpassword'), 'admin@example.com', 1))  # Set is_admin to 1 for admin user
        conn.commit()

    conn.commit()
    conn.close()

# Email function to send enrollment confirmation
def send_email(to_email, course_name):
    msg = MIMEMultipart()
    msg['From'] = 'your_email@example.com'
    msg['To'] = to_email
    msg['Subject'] = 'Enrollment Confirmation'
    body = f'You have successfully enrolled in {course_name}.'
    msg.attach(MIMEText(body, 'plain'))
    
    with smtplib.SMTP('smtp.example.com', 587) as server:
        server.starttls()
        server.login('vennilag84@gmail.com', 'Billgates@123')
        server.send_message(msg)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Database connection
        conn = sqlite3.connect('courses.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password, is_admin FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        # Verify user
        if user and check_password_hash(user[2], password):
            user_id, _, _, is_admin = user
            if is_admin == 1:  # Admin
                return redirect(url_for('admin'))
            else:  # Regular user
                return redirect(url_for('user'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('login.html')

@app.route('/courses')
def courses():
    return render_template('courses.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        hashed_password = generate_password_hash(password)  # Hash the password
        conn = sqlite3.connect('courses.db')
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)', 
                           (username, hashed_password, email))
            conn.commit()
            flash('Registration successful')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists')
        conn.close()
    return render_template('register.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        course_name = request.form['course_name']
        course_details = request.form['course_details']
        course_materials = request.form['course_materials']
        conn = sqlite3.connect('courses.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO courses (name, details, materials) VALUES (?, ?, ?)', 
                       (course_name, course_details, course_materials))
        conn.commit()
        conn.close()
        flash('Course added successfully')
    return render_template('admin.html')

@app.route('/user')
def user():
    conn = sqlite3.connect('courses.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM courses')
    courses = cursor.fetchall()
    conn.close()
    return render_template('user.html', courses=courses)

@app.route('/enroll/<int:course_id>')
def enroll(course_id):
    user_id = 1  # Replace with actual logged-in user ID
    conn = sqlite3.connect('courses.db')
    cursor = conn.cursor()

    # Check if the user is already enrolled in the course
    cursor.execute('SELECT * FROM enrollments WHERE user_id = ? AND course_id = ?', (user_id, course_id))
    enrollment = cursor.fetchone()
    
    if enrollment:
        flash('You are already enrolled in this course.')
        return redirect(url_for('user'))

    cursor.execute('SELECT name FROM courses WHERE id = ?', (course_id,))
    course = cursor.fetchone()
    cursor.execute('SELECT email FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    if course and user:
        course_name = course[0]
        user_email = user[0]
        cursor.execute('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', (user_id, course_id))
        conn.commit()
        send_email(user_email, course_name)
        flash('Successfully enrolled and confirmation email sent!')
    else:
        flash('Error enrolling in course')

    conn.close()
    return redirect(url_for('user'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
