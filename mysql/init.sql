-- init.sql
CREATE DATABASE IF NOT EXISTS college_db;
USE college_db;

-- ADMIN
CREATE TABLE IF NOT EXISTS admin (
  admin_id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL
);

-- FACULTY
CREATE TABLE IF NOT EXISTS faculty (
  faculty_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(100) UNIQUE,
  dept VARCHAR(50),
  phone VARCHAR(15),
  password VARCHAR(255) NOT NULL
);

-- STUDENT
CREATE TABLE IF NOT EXISTS student (
  student_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  dob DATE,
  email VARCHAR(100) UNIQUE,
  dept VARCHAR(50),
  year INT,
  phone VARCHAR(15),
  password VARCHAR(255) NOT NULL
);

-- COURSE
CREATE TABLE IF NOT EXISTS course (
  course_id INT AUTO_INCREMENT PRIMARY KEY,
  course_name VARCHAR(100) NOT NULL,
  dept VARCHAR(50),
  credits INT,
  faculty_id INT,
  FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id) ON DELETE SET NULL
);

-- ENROLLMENT (bridge table)
CREATE TABLE IF NOT EXISTS enrollment (
  enroll_id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  course_id INT NOT NULL,
  year INT,
  semester VARCHAR(10),
  UNIQUE KEY unique_enroll (student_id, course_id),
  FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE,
  FOREIGN KEY (course_id) REFERENCES course(course_id) ON DELETE CASCADE
);

-- ATTENDANCE
CREATE TABLE IF NOT EXISTS attendance (
  attend_id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  course_id INT NOT NULL,
  date DATE NOT NULL,
  status ENUM('Present','Absent') NOT NULL,
  FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE,
  FOREIGN KEY (course_id) REFERENCES course(course_id) ON DELETE CASCADE
);

-- RESULT
CREATE TABLE IF NOT EXISTS result (
  result_id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  course_id INT NOT NULL,
  marks DECIMAL(5,2),
  grade VARCHAR(5),
  FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE,
  FOREIGN KEY (course_id) REFERENCES course(course_id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_attendance_date ON attendance(date);
CREATE INDEX idx_enrollment_student ON enrollment(student_id);
CREATE INDEX idx_result_student ON result(student_id);

-- Seed: admin (password will be hashed later with seed.py)
INSERT INTO admin (username, password) VALUES ('admin', 'admin123');

-- Seed example faculty and students with simple passwords (will be hashed by seed.py)
INSERT INTO faculty (name, email, dept, phone, password)
VALUES ('Dr. Patel','patel@college.edu','Computer','9876543210','facpass');

INSERT INTO student (name, dob, email, dept, year, phone, password)
VALUES ('Amit Kumar','2002-05-12','amit@college.edu','Computer',3,'9123456789','studpass');

-- Example course and enrollment
INSERT INTO course (course_name, dept, credits, faculty_id) VALUES ('Database Systems','Computer',3,1);
INSERT INTO enrollment (student_id, course_id, year, semester) VALUES (1,1,2025,'Sem 1');
