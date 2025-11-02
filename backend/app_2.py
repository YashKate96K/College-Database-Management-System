from flask import Flask, render_template, request, redirect, session, url_for, flash
import mysql.connector
from functools import wraps
from datetime import date

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------------------
# DB Connection
# ---------------------------
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="y@shkate96K",
        database="college_db"
    )

# ---------------------------
# Login Required Decorator
# ---------------------------
def login_required(role=None):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                flash("Please log in first!", "danger")
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash("Unauthorized Access", "danger")
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

# ---------------------------
# Routes
# ---------------------------

@app.route('/')
def index():
    return redirect('/login')

# ---------------------------
# LOGIN
# ---------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        if role == "admin":
            cur.execute("SELECT * FROM admin WHERE username=%s AND password=%s", (username, password))
        elif role == "faculty":
            cur.execute("SELECT * FROM faculty WHERE email=%s AND password=%s", (username, password))
        elif role == "student":
            cur.execute("SELECT * FROM student WHERE email=%s AND password=%s", (username, password))

        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session['user'] = user
            session['role'] = role
            if role == 'admin':
                return redirect('/admin_dashboard')
            elif role == 'faculty':
                return redirect('/faculty_dashboard')
            elif role == 'student':
                return redirect('/student_dashboard')
        else:
            return render_template('login.html', msg="Invalid username/email, password, or role")

    return render_template('login.html')


# ---------------------------
# ADMIN DASHBOARD
# ---------------------------
@app.route('/admin_dashboard')
@login_required(role='admin')
def admin_dashboard():
    return render_template('admin_dashboard.html')

# Add Student + Enrollment
@app.route('/admin/add_student', methods=['GET', 'POST'])
@login_required(role='admin')
def add_student():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        dept = request.form['dept']
        course_id = request.form['course_id']

        cur.execute("INSERT INTO student (name, email, password, dept, year) VALUES (%s,%s,%s,%s,%s)", 
                    (name, email, password, dept, 1))
        student_id = cur.lastrowid

        cur.execute("INSERT INTO enrollment (student_id, course_id, year, semester) VALUES (%s,%s,%s,%s)",
                    (student_id, course_id, 2025, 'Sem 1'))

        conn.commit()
        flash("Student added and enrolled successfully!", "success")
        cur.close(); conn.close()
        return redirect('/admin_dashboard')

    cur.execute("SELECT * FROM course")
    courses = cur.fetchall()
    cur.close(); conn.close()
    return render_template('add_student.html', courses=courses)

# Add Faculty
@app.route('/admin/add_faculty', methods=['GET', 'POST'])
@login_required(role='admin')
def add_faculty():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        dept = request.form['dept']
        phone = request.form['phone']
        password = request.form['password']

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO faculty (name, email, dept, phone, password) VALUES (%s,%s,%s,%s,%s)",
                    (name, email, dept, phone, password))
        conn.commit()
        cur.close(); conn.close()
        flash("Faculty added successfully!", "success")
        return redirect('/admin_dashboard')
    return render_template('add_faculty.html')


# Assign Course to Faculty
@app.route('/admin/assign_course', methods=['GET', 'POST'])
@login_required(role='admin')
def assign_course():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        course_name = request.form['course_name']
        dept = request.form['dept']
        credits = request.form['credits']
        faculty_id = request.form['faculty_id']
        cur.execute("INSERT INTO course (course_name, dept, credits, faculty_id) VALUES (%s,%s,%s,%s)",
                    (course_name, dept, credits, faculty_id))
        conn.commit()
        flash("Course assigned successfully!", "success")
        cur.close(); conn.close()
        return redirect('/admin_dashboard')

    cur.execute("SELECT * FROM faculty")
    faculty = cur.fetchall()
    cur.close(); conn.close()
    return render_template('assign_course.html', faculty=faculty)

# ---------------------------
# FACULTY DASHBOARD
# ---------------------------
@app.route('/faculty_dashboard')
@login_required(role='faculty')
def faculty_dashboard():
    faculty_id = session['user']['faculty_id']
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM course WHERE faculty_id=%s", (faculty_id,))
    courses = cur.fetchall()
    cur.close(); conn.close()
    return render_template('faculty_dashboard.html', courses=courses)

# Attendance marking
@app.route('/faculty/attendance/<int:course_id>', methods=['GET', 'POST'])
@login_required(role='faculty')
def mark_attendance(course_id):
    conn = get_connection(); cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        date_str = request.form.get('date') or str(date.today())
        cur.execute("SELECT s.student_id FROM student s JOIN enrollment e ON s.student_id=e.student_id WHERE e.course_id=%s", (course_id,))
        for s in cur.fetchall():
            sid = s['student_id']
            status = 'Present' if request.form.get(f'present_{sid}') else 'Absent'
            cur.execute("INSERT INTO attendance (student_id, course_id, date, status) VALUES (%s,%s,%s,%s)",
                        (sid, course_id, date_str, status))
        conn.commit(); cur.close(); conn.close()
        flash('Attendance recorded successfully!', 'success')
        return redirect('/faculty_dashboard')

    cur.execute("""SELECT s.student_id, s.name 
                   FROM student s JOIN enrollment e ON s.student_id=e.student_id 
                   WHERE e.course_id=%s""", (course_id,))
    students = cur.fetchall()
    cur.close(); conn.close()
    return render_template('attendance_mark.html', students=students, course_id=course_id)

# Upload results
@app.route('/faculty/results/<int:course_id>', methods=['GET', 'POST'])
@login_required(role='faculty')
def upload_results(course_id):
    conn = get_connection(); cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        cur.execute("SELECT s.student_id FROM student s JOIN enrollment e ON s.student_id=e.student_id WHERE e.course_id=%s", (course_id,))
        for s in cur.fetchall():
            sid = s['student_id']
            marks = request.form.get(f'marks_{sid}')
            grade = request.form.get(f'grade_{sid}')
            if marks:
                cur.execute("""INSERT INTO result (student_id, course_id, marks, grade)
                            VALUES (%s,%s,%s,%s)
                            ON DUPLICATE KEY UPDATE marks=VALUES(marks), grade=VALUES(grade)""",
                            (sid, course_id, marks, grade))
        conn.commit(); cur.close(); conn.close()
        flash('Results uploaded successfully!', 'success')
        return redirect('/faculty_dashboard')

    cur.execute("""SELECT s.student_id, s.name 
                   FROM student s JOIN enrollment e ON s.student_id=e.student_id 
                   WHERE e.course_id=%s""", (course_id,))
    students = cur.fetchall()
    cur.close(); conn.close()
    return render_template('upload_results.html', students=students, course_id=course_id)

# ---------------------------
# STUDENT DASHBOARD
# ---------------------------
@app.route('/student_dashboard')
@login_required(role='student')
def student_dashboard():
    student_id = session['user']['student_id']
    conn = get_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("""SELECT c.course_name, r.marks, r.grade 
                   FROM result r JOIN course c ON r.course_id=c.course_id
                   WHERE r.student_id=%s""", (student_id,))
    results = cur.fetchall()
    cur.close(); conn.close()
    return render_template('student_dashboard.html', results=results)

# ---------------------------
# LOGOUT
# ---------------------------
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect('/login')

# ---------------------------
# RUN
# ---------------------------
if __name__ == '__main__':
    app.run(debug=True)
