from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas


# -------------------------
# Departments
# -------------------------

def create_department(db: Session, department: schemas.DepartmentCreate):
    db_department = models.Department(**department.model_dump())
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return db_department


def get_department(db: Session, department_id: int):
    return db.get(models.Department, department_id)


def get_departments(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    after_id: int | None = None,
):
    statement = select(models.Department).order_by(models.Department.id)

    if after_id is not None:
        statement = statement.where(models.Department.id > after_id)
    else:
        statement = statement.offset(skip)

    statement = statement.limit(limit)
    return db.scalars(statement).all()


def update_department(db: Session, department_id: int, updates: dict):
    department = db.get(models.Department, department_id)
    if department is None:
        return None

    for field, value in updates.items():
        setattr(department, field, value)

    db.commit()
    db.refresh(department)
    return department


def delete_department(db: Session, department_id: int):
    department = db.get(models.Department, department_id)
    if department is None:
        return False

    db.delete(department)
    db.commit()
    return True


# -------------------------
# Lecturers
# -------------------------

def create_lecturer(db: Session, lecturer: schemas.LecturerCreate):
    db_lecturer = models.Lecturer(**lecturer.model_dump())
    db.add(db_lecturer)
    db.commit()
    db.refresh(db_lecturer)
    return db_lecturer


def get_lecturer(db: Session, lecturer_id: int):
    return db.get(models.Lecturer, lecturer_id)


def get_lecturers(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    after_id: int | None = None,
):
    statement = select(models.Lecturer).order_by(models.Lecturer.id)

    if after_id is not None:
        statement = statement.where(models.Lecturer.id > after_id)
    else:
        statement = statement.offset(skip)

    statement = statement.limit(limit)
    return db.scalars(statement).all()


def update_lecturer(db: Session, lecturer_id: int, updates: dict):
    lecturer = db.get(models.Lecturer, lecturer_id)
    if lecturer is None:
        return None

    for field, value in updates.items():
        setattr(lecturer, field, value)

    db.commit()
    db.refresh(lecturer)
    return lecturer


def delete_lecturer(db: Session, lecturer_id: int):
    lecturer = db.get(models.Lecturer, lecturer_id)
    if lecturer is None:
        return False

    db.delete(lecturer)
    db.commit()
    return True


# -------------------------
# Courses
# -------------------------

def create_course(db: Session, course: schemas.CourseCreate):
    db_course = models.Course(**course.model_dump())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course


def get_course(db: Session, course_id: int):
    return db.get(models.Course, course_id)


def get_courses(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    after_id: int | None = None,
):
    statement = select(models.Course).order_by(models.Course.id)

    if after_id is not None:
        statement = statement.where(models.Course.id > after_id)
    else:
        statement = statement.offset(skip)

    statement = statement.limit(limit)
    return db.scalars(statement).all()


def update_course(db: Session, course_id: int, updates: dict):
    course = db.get(models.Course, course_id)
    if course is None:
        return None

    for field, value in updates.items():
        setattr(course, field, value)

    db.commit()
    db.refresh(course)
    return course


def delete_course(db: Session, course_id: int):
    course = db.get(models.Course, course_id)
    if course is None:
        return False

    db.delete(course)
    db.commit()
    return True


# -------------------------
# Exams
# -------------------------

def create_exam(db: Session, exam: schemas.ExamCreate):
    db_exam = models.Exam(**exam.model_dump())
    db.add(db_exam)
    db.commit()
    db.refresh(db_exam)
    return db_exam


def get_exam(db: Session, exam_id: int):
    return db.get(models.Exam, exam_id)


def get_exams(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    after_id: int | None = None,
):
    statement = select(models.Exam).order_by(models.Exam.id)

    if after_id is not None:
        statement = statement.where(models.Exam.id > after_id)
    else:
        statement = statement.offset(skip)

    statement = statement.limit(limit)
    return db.scalars(statement).all()


def update_exam(db: Session, exam_id: int, updates: dict):
    exam = db.get(models.Exam, exam_id)
    if exam is None:
        return None

    for field, value in updates.items():
        setattr(exam, field, value)

    db.commit()
    db.refresh(exam)
    return exam


def delete_exam(db: Session, exam_id: int):
    exam = db.get(models.Exam, exam_id)
    if exam is None:
        return False

    db.delete(exam)
    db.commit()
    return True
