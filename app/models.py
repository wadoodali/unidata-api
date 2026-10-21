from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)


class Lecturer(Base):
    __tablename__ = "lecturers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)

    department_id = Column(
        Integer,
        ForeignKey("departments.id"),
        nullable=False,
    )

    department = relationship("Department")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    course_code = Column(String(20), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    ects = Column(Integer, nullable=False)

    department_id = Column(
        Integer,
        ForeignKey("departments.id"),
        nullable=False,
    )

    lecturer_id = Column(
        Integer,
        ForeignKey("lecturers.id"),
        nullable=False,
    )

    department = relationship("Department")
    lecturer = relationship("Lecturer")


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    exam_date = Column(DateTime, nullable=False)
    room = Column(String(50), nullable=False)

    course_id = Column(
        Integer,
        ForeignKey("courses.id"),
        nullable=False,
    )

    course = relationship("Course")
