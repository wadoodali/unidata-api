import argparse
import random
from datetime import datetime, timedelta

from sqlalchemy import func, select

from app import models
from app.database import Base, SessionLocal, engine


DEPARTMENT_TARGET = 1_000
LECTURER_TARGET = 10_000
COURSE_TARGET = 500_000
EXAM_TARGET = 500_000


def count_records(db, model):
    return db.scalar(
        select(func.count()).select_from(model)
    ) or 0


def commit_batches(db, records, batch_size):
    for start in range(0, len(records), batch_size):
        db.add_all(records[start:start + batch_size])
        db.commit()


def generate_data(batch_size: int = 1000):
    random.seed(42)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        # 1. Departments: fill to target without duplicate names.
        existing_names = set(
            db.scalars(select(models.Department.name)).all()
        )

        department_number = 1
        while count_records(db, models.Department) < DEPARTMENT_TARGET:
            needed = DEPARTMENT_TARGET - count_records(
                db, models.Department
            )
            batch = []

            while len(batch) < min(batch_size, needed):
                name = f"Benchmark Department {department_number:05d}"
                department_number += 1

                if name in existing_names:
                    continue

                existing_names.add(name)
                batch.append(models.Department(name=name))

            db.add_all(batch)
            db.commit()

        departments = db.scalars(
            select(models.Department).order_by(models.Department.id)
        ).all()
        print(f"Departments: {count_records(db, models.Department):,}")

        # 2. Lecturers: fill to target without duplicate emails.
        existing_emails = set(
            db.scalars(select(models.Lecturer.email)).all()
        )

        lecturer_number = 1
        while count_records(db, models.Lecturer) < LECTURER_TARGET:
            needed = LECTURER_TARGET - count_records(
                db, models.Lecturer
            )
            batch = []

            while len(batch) < min(batch_size, needed):
                email = (
                    f"benchmark.lecturer.{lecturer_number:08d}"
                    "@example.com"
                )
                name = f"Benchmark Lecturer {lecturer_number:08d}"
                lecturer_number += 1

                if email in existing_emails:
                    continue

                existing_emails.add(email)
                batch.append(
                    models.Lecturer(
                        name=name,
                        email=email,
                        department_id=random.choice(departments).id,
                    )
                )

            db.add_all(batch)
            db.commit()

        lecturers = db.scalars(
            select(models.Lecturer).order_by(models.Lecturer.id)
        ).all()
        print(f"Lecturers:  {count_records(db, models.Lecturer):,}")

        # 3. Courses: track unique course codes explicitly.
        existing_codes = set(
            db.scalars(select(models.Course.course_code)).all()
        )

        course_number = 1
        while count_records(db, models.Course) < COURSE_TARGET:
            needed = COURSE_TARGET - count_records(
                db, models.Course
            )
            batch = []

            while len(batch) < min(batch_size, needed):
                code = f"BENCH{course_number:08d}"
                title = f"Benchmark Course {course_number}"
                course_number += 1

                if code in existing_codes:
                    continue

                existing_codes.add(code)
                batch.append(
                    models.Course(
                        course_code=code,
                        title=title,
                        ects=random.choice([3, 5, 6, 10]),
                        department_id=random.choice(departments).id,
                        lecturer_id=random.choice(lecturers).id,
                    )
                )

            db.add_all(batch)
            db.commit()

        print(f"Courses:    {count_records(db, models.Course):,}")

        # 4. Exams: each exam references an existing course.
        course_ids = db.scalars(
            select(models.Course.id).order_by(models.Course.id)
        ).all()

        if not course_ids and EXAM_TARGET > 0:
            raise RuntimeError("Cannot generate exams without courses.")

        base_date = datetime(2026, 1, 1)

        while count_records(db, models.Exam) < EXAM_TARGET:
            needed = EXAM_TARGET - count_records(db, models.Exam)
            batch_count = min(batch_size, needed)

            exams = [
                models.Exam(
                    exam_date=base_date + timedelta(
                        days=random.randint(0, 364)
                    ),
                    room=f"Room {random.randint(1, 200):03d}",
                    course_id=random.choice(course_ids),
                )
                for _ in range(batch_count)
            ]

            db.add_all(exams)
            db.commit()

        print(f"Exams:      {count_records(db, models.Exam):,}")
        print("Benchmark data generation complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=1000)
    args = parser.parse_args()

    if args.batch_size < 1:
        parser.error("--batch-size must be positive")

    generate_data(batch_size=args.batch_size)
