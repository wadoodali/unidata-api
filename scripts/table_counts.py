
from sqlalchemy import func, select

from app.database import SessionLocal
from app.models import Department, Lecturer, Course, Exam


def main():
    tables = [
        ("Departments", Department),
        ("Lecturers", Lecturer),
        ("Courses", Course),
        ("Exams", Exam),
    ]

    with SessionLocal() as db:
        for name, model in tables:
            count = db.scalar(
                select(func.count()).select_from(model)
            )
            print(f"{name:12} {count:>10,} records")


if __name__ == "__main__":
    main()
