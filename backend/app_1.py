import os
from flask import Flask, render_template, request, redirect, session, url_for, flash
from db_config import get_connection
from datetime import date

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'devsecret')

# ---- Helpers ----
def login_required(role=None):
    def wrapper(fn):
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash('Unauthorized', 'danger')
                return redirect(url_for('login'))
            return fn(*args, **kwargs)
        decorated.__name__ = fn.__name__
        return decorated
    return wrapper

# ---- Routes ----
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        role = request.form['role']
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        if role == 'admin':
            cur.execute("SELECT * FROM admin WHERE username=%s", (username,))
        elif role == 'faculty':
            cur.execute("SELECT * FROM faculty WHERE email=%s", (username,))
        else:  # student
            cur.execute("SELECT * FROM student WHERE email=%s", (username,))

        user = cur.fetchone()
        cur.close(); conn.close()

        # Plain text password check
        if user and user['password'] == password:
            session['user_id'] = user.get('admin_id') or user.get('faculty_id') or user.get('student_id')
            session['role'] = role
            session['username'] = username
            if role=='admin': return redirect(url_for('admin_dashboard'))
            if role=='faculty': return redirect(url_for('faculty_dashboard'))
            return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---- Admin Dashboard ----
@app.route('/admin')
@login_required(role='admin')
def admin_dashboard():
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM student")
    students_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM faculty")
    faculty_count = cur.fetchone()[0] 
    cur.execute("SELECT COUNT(*) FROM course")  # ✅ Add this line
    courses_count = cur.fetchone()[0]
    cur.close(); conn.close()
    return render_template('admin_dashboard.html', students_count=students_count, faculty_count=faculty_count,courses_count=courses_count)

# Student CRUD
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

        # Insert student
        cur.execute("""
            INSERT INTO student (name, dob, email, dept, year, phone, password)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, dob, email, dept, year, phone, password))
        sid = cur.lastrowid

        # Enroll automatically into all department courses (optional logic)
        cur.execute("SELECT course_id FROM course WHERE dept=%s", (dept,))
        for (cid,) in cur.fetchall():
            cur.execute("""
                INSERT INTO enrollment (student_id, course_id, year, semester)
                VALUES (%s, %s, %s, %s)
            """, (sid, cid, year, 'Sem 1'))

        conn.commit()
        cur.close()
        conn.close()

        flash('Student added and enrolled successfully!', 'success')
        return redirect(url_for('students_list'))

    return render_template('add_student.html')




# Courses
@app.route('/admin/courses')
@login_required(role='admin')
def courses_list():
    conn = get_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("""SELECT c.*, f.name as faculty_name FROM course c LEFT JOIN faculty f ON c.faculty_id = f.faculty_id""")
    courses = cur.fetchall()
    cur.close(); conn.close()
    return render_template('courses_list.html', courses=courses)

@app.route('/admin/courses/add', methods=['GET','POST'])
@login_required(role='admin')
def add_course():
    conn = get_connection(); cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        cname = request.form['course_name']; dept = request.form['dept']
        credits = request.form.get('credits') or None; faculty_id = request.form.get('faculty_id') or None
        cur.execute("INSERT INTO course (course_name,dept,credits,faculty_id) VALUES (%s,%s,%s,%s)",
                    (cname, dept, credits, faculty_id))
        conn.commit()
        cur.close(); conn.close()
        flash('Course added', 'success')
        return redirect(url_for('courses_list'))
    cur.execute("SELECT faculty_id, name FROM faculty")
    faculties = cur.fetchall()
    cur.close(); conn.close()
    return render_template('add_course.html', faculties=faculties)

# ---- Faculty Dashboard ----
@app.route('/faculty')
@login_required(role='faculty')
def faculty_dashboard():
    fid = session.get('user_id')
    conn = get_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM course WHERE faculty_id=%s", (fid,))
    courses = cur.fetchall()
    cur.close(); conn.close()
    return render_template('faculty_dashboard.html', courses=courses)

# Mark attendance (faculty)
@app.route('/faculty/attendance/<int:course_id>', methods=['GET','POST'])
@login_required(role='faculty')
def mark_attendance(course_id):
    if request.method == 'POST':
        date_str = request.form.get('date') or str(date.today())
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT s.student_id FROM student s JOIN enrollment e ON s.student_id=e.student_id WHERE e.course_id=%s", (course_id,))
        stu_rows = cur.fetchall()
        for (sid,) in stu_rows:
            status = 'Present' if request.form.get(f'present_{sid}') == 'on' else 'Absent'
            cur.execute("INSERT INTO attendance (student_id, course_id, date, status) VALUES (%s,%s,%s,%s)",
                        (sid, course_id, date_str, status))
        conn.commit(); cur.close(); conn.close()
        flash('Attendance saved', 'success')
        return redirect(url_for('faculty_dashboard'))
    conn = get_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("""SELECT s.student_id, s.name FROM student s
                   JOIN enrollment e ON s.student_id=e.student_id
                   WHERE e.course_id=%s""", (course_id,))
    students = cur.fetchall()
    cur.close(); conn.close()
    return render_template('attendance_mark.html', students=students, course_id=course_id)

# ---- Student Dashboard ----
@app.route('/student')
@login_required(role='student')
def student_dashboard():
    sid = session.get('user_id')
    conn = get_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT 
            c.course_id,
            c.course_name,
            IFNULL(a.present_count, 0) AS presents,
            IFNULL(a.total_count, 0) AS total,
            r.marks,
            r.grade
        FROM course c
        JOIN enrollment e ON c.course_id = e.course_id
        LEFT JOIN (
            SELECT course_id, student_id,
                   SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) AS present_count,
                   COUNT(*) AS total_count
            FROM attendance
            GROUP BY course_id, student_id
        ) a ON a.course_id = c.course_id AND a.student_id = e.student_id
        LEFT JOIN result r ON r.course_id = c.course_id AND r.student_id = e.student_id
        WHERE e.student_id = %s
    """, (sid,))
    rows = cur.fetchall()
    cur.close(); conn.close()

    # Calculate attendance percentage
    for r in rows:
        total = r['total'] or 0
        r['attendance_pct'] = round((r['presents'] / total * 100) if total > 0 else 0, 2)

    return render_template('student_dashboard.html', courses=rows)


# ---- Results upload (faculty)
@app.route('/faculty/results/<int:course_id>', methods=['GET','POST'])
@login_required(role='faculty')
def upload_results(course_id):
    if request.method == 'POST':
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT s.student_id FROM student s JOIN enrollment e ON s.student_id=e.student_id WHERE e.course_id=%s", (course_id,))
        stu_rows = cur.fetchall()
        for (sid,) in stu_rows:
            marks = request.form.get(f'marks_{sid}')
            grade = request.form.get(f'grade_{sid}')
            if marks is not None:
                cur.execute("INSERT INTO result (student_id, course_id, marks, grade) VALUES (%s,%s,%s,%s)",
                            (sid, course_id, marks, grade))
        conn.commit(); cur.close(); conn.close()
        flash('Results uploaded', 'success')
        return redirect(url_for('faculty_dashboard'))
    conn = get_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("""SELECT s.student_id, s.name FROM student s JOIN enrollment e ON s.student_id=e.student_id WHERE e.course_id=%s""", (course_id,))
    students = cur.fetchall()
    cur.close(); conn.close()
    return render_template('results_upload.html', students=students, course_id=course_id)

# ---- Run ----
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
