from sqlalchemy import Column, Integer, String, Date, DECIMAL, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Admin(Base):
    __tablename__ = 'admin'
    admin_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

class Faculty(Base):
    __tablename__ = 'faculty'
    faculty_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    dept = Column(String(50))
    phone = Column(String(15))
    password = Column(String(255), nullable=False)

class Student(Base):
    __tablename__ = 'student'
    student_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    dob = Column(Date)
    email = Column(String(100), unique=True)
    dept = Column(String(50))
    year = Column(Integer)
    phone = Column(String(15))
    password = Column(String(255), nullable=False)

class Course(Base):
    __tablename__ = 'course'
    course_id = Column(Integer, primary_key=True, autoincrement=True)
    course_name = Column(String(100), nullable=False)
    dept = Column(String(50))
    credits = Column(Integer)
    faculty_id = Column(Integer, ForeignKey('faculty.faculty_id'))
