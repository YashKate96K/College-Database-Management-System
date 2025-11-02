import os
from flask import Flask, render_template, request, redirect, session, url_for, flash
from db_config import get_connection
from datetime import date
from functools import wraps

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'devsecret')

# -------------------------------------
# Helper: login_required decorator
# -------------------------------------
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please login first', 'warning')
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash('Unauthorized access', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# -------------------------------------
# Home / Login / Logout
# -------------------------------------
@app.route('/')
def home():
    if 'role' in session:
        if session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif session['role'] == 'faculty':
            return redirect(url_for('faculty_dashboard'))
        elif session['role'] == 'student':
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        role = request.form['role']

        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        query_map = {
            'admin': "SELECT * FROM admin WHERE username=%s",
            'faculty': "SELECT * FROM faculty WHERE email=%s",
            'student': "SELECT * FROM student WHERE email=%s"
        }

        cur.execute(query_map[role], (username,))
        user = cur.fetchone()
        cur.close(); conn.close()

        if user and user['password'] == password:
            session['user_id'] = user.get('admin_id') or user.get('faculty_id') or user.get('student_id')
            session['role'] = role
            session['username'] = username

            if role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif role == 'faculty':
                return redirect(url_for('faculty_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# -------------------------------------
# Admin Dashboard
# -------------------------------------
@app.route('/admin')
@login_required(role='admin')
def admin_dashboard():
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM student")
    students_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM faculty")
    faculty_count = cur.fetchone()[0]
    cur.close(); conn.close()
    return render_template('admin_dashboard.html', students_count=students_count, faculty_count=faculty_count)

# ---- Student CRUD ----
@app.route('/admin/students')
@login_required(role='admin')
def students_list():
    conn = get_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM student")
    students = cur.fetchall()
    cur.close(); conn.close()
    return render_template('students_list.html', students=students)

@app.route('/admin/students/add', methods=['GET', 'POST'])
@login_required(role='admin')
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        dob = request.form.get('dob') or None
        email = request.form['email']
        dept = request.form['dept']
        year = request.form.get('year') or None
        phone = request.form.get('phone') or None
        password = request.form.get('password', 'default123')

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO student (name, dob, email, dept, year, phone, password)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, dob, email, dept, year, phone, password))
        student_id = cur.lastrowid

        # Auto-enroll in department courses
        cur.execute("""
            INSERT INTO enrollment (student_id, course_id)
            SELECT %s, c.course_id FROM course c
            WHERE c.dept = %s
            AND NOT EXISTS (
                SELECT 1 FROM enrollment e WHERE e.student_id=%s AND e.course_id=c.course_id
            )
        """, (student_id, dept, student_id))
        conn.commit()

        cur.close(); conn.close()
        flash('Student added and enrolled in department courses.', 'success')
        return redirect(url_for('students_list'))
    return render_template('add_student.html')

# ---- Courses ----
@app.route('/admin/courses')
@login_required(role='admin')
def courses_list():
    conn = get_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT c.*, f.name AS faculty_name 
        FROM course c 
        LEFT JOIN faculty f ON c.faculty_id = f.faculty_id
    """)
    courses = cur.fetchall()
    cur.close(); conn.close()
    return render_template('courses_list.html', courses=courses)

@app.route('/admin/courses/add', methods=['GET', 'POST'])
@login_required(role='admin')
def add_course():
    conn = get_connection(); cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        cname = request.form['course_name']
        dept = request.form['dept']
        credits = request.form.get('credits') or None
        faculty_id = request.form.get('faculty_id') or None
        cur.execute("INSERT INTO course (course_name, dept, credits, faculty_id) VALUES (%s, %s, %s, %s)",
                    (cname, dept, credits, faculty_id))
        conn.commit()
        cur.close(); conn.close()
        flash('Course added successfully.', 'success')
        return redirect(url_for('courses_list'))
    cur.execute("SELECT faculty_id, name FROM faculty")
    faculties = cur.fetchall()
    cur.close(); conn.close()
    return render_template('add_course.html', faculties=faculties)

# -------------------------------------
# Faculty Dashboard
# -------------------------------------
@app.route('/faculty')
@login_required(role='faculty')
def faculty_dashboard():
    fid = session.get('user_id')
    conn = get_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM course WHERE faculty_id=%s", (fid,))
    courses = cur.fetchall()
    cur.close(); conn.close()
    return render_template('faculty_dashboard.html', courses=courses)

# Attendance marking
@app.route('/faculty/attendance/<int:course_id>', methods=['GET', 'POST'])
@login_required(role='faculty')
def mark_attendance(course_id):
    conn = get_connection(); cur = conn.cursor()
    if request.method == 'POST':
        date_str = request.form.get('date') or str(date.today())
        cur.execute("""
            SELECT s.student_id FROM student s
            JOIN enrollment e ON s.student_id=e.student_id
            WHERE e.course_id=%s
        """, (course_id,))
        for (sid,) in cur.fetchall():
            status = 'Present' if request.form.get(f'present_{sid}') else 'Absent'
            cur.execute("INSERT INTO attendance (student_id, course_id, date, status) VALUES (%s, %s, %s, %s)",
                        (sid, course_id, date_str, status))
        conn.commit()
        cur.close(); conn.close()
        flash('Attendance recorded successfully.', 'success')
        return redirect(url_for('faculty_dashboard'))

    cur.execute("""
        SELECT s.student_id, s.name 
        FROM student s 
        JOIN enrollment e ON s.student_id=e.student_id 
        WHERE e.course_id=%s
    """, (course_id,))
    students = cur.fetchall()
    cur.close(); conn.close()
    return render_template('attendance_mark.html', students=students, course_id=course_id)

# Results Upload
@app.route('/faculty/results/<int:course_id>', methods=['GET', 'POST'])
@login_required(role='faculty')
def upload_results(course_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    if request.method == 'POST':
        # Fetch all enrolled student IDs
        cur.execute("""
            SELECT s.student_id 
            FROM student s 
            JOIN enrollment e ON s.student_id = e.student_id 
            WHERE e.course_id = %s
        """, (course_id,))
        for row in cur.fetchall():
            sid = row['student_id']
            marks_str = request.form.get(f'marks_{sid}', '').strip()
            grade = request.form.get(f'grade_{sid}', '').strip()

            if marks_str:
                try:
                    marks = float(marks_str)
                    cur.execute("""
                        INSERT INTO result (student_id, course_id, marks, grade)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE marks=VALUES(marks), grade=VALUES(grade)
                    """, (sid, course_id, marks, grade))
                except ValueError:
                    flash(f'Invalid marks for student ID {sid}', 'danger')

        conn.commit()
        flash('Results uploaded successfully.', 'success')
        cur.close()
        conn.close()
        return redirect(url_for('faculty_dashboard'))

    # -------------------------
    # GET request — fetch student details (names)
    # -------------------------
    cur.execute("""
        SELECT s.student_id, s.name
        FROM student s
        JOIN enrollment e ON s.student_id = e.student_id
        WHERE e.course_id = %s
    """, (course_id,))
    students = cur.fetchall()

    cur.close()
    conn.close()
    return render_template('results_upload.html', students=students)


# -------------------------------------
# Student Dashboard
# -------------------------------------
@app.route('/student')
@login_required(role='student')
def student_dashboard():
    sid = session.get('user_id')
    conn = get_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT c.course_name,
               (SELECT COUNT(*) FROM attendance a WHERE a.student_id=%s AND a.course_id=c.course_id AND a.status='Present') AS presents,
               (SELECT COUNT(*) FROM attendance a WHERE a.student_id=%s AND a.course_id=c.course_id) AS total,
               (SELECT r.marks FROM result r WHERE r.student_id=%s AND r.course_id=c.course_id) AS marks,
               (SELECT r.grade FROM result r WHERE r.student_id=%s AND r.course_id=c.course_id) AS grade
        FROM course c 
        JOIN enrollment e ON c.course_id=e.course_id
        WHERE e.student_id=%s
    """, (sid, sid, sid, sid, sid))
    rows = cur.fetchall()
    cur.close(); conn.close()

    for r in rows:
        total = r['total'] or 0
        r['attendance_pct'] = round((r['presents']/total*100) if total else 0, 2)

    return render_template('student_dashboard.html', courses=rows)

# -------------------------------------
# Run the App
# -------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
