import statistics
import time

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Department, Lecturer, Course, Exam


RUNS = 10
PAGE_SIZE = 20

MODELS = [
    ("Departments", Department),
    ("Lecturers", Lecturer),
    ("Courses", Course),
    ("Exams", Exam),
]


def measure(query_factory):
    timings = []

    with SessionLocal() as db:
        query_factory(db).all()  # Warm-up

        for _ in range(RUNS):
            start = time.perf_counter()
            query_factory(db).all()
            timings.append((time.perf_counter() - start) * 1000)

    return statistics.mean(timings)


def offset_query(db, model, offset):
    statement = (
        select(model)
        .order_by(model.id)
        .offset(offset)
        .limit(PAGE_SIZE)
    )
    return db.scalars(statement)


def keyset_query(db, model, last_id):
    statement = (
        select(model)
        .where(model.id > last_id)
        .order_by(model.id)
        .limit(PAGE_SIZE)
    )
    return db.scalars(statement)


def benchmark_table(db, name, model):
    total = db.scalar(
        select(model.id).order_by(model.id.desc()).limit(1)
    )

    if total is None:
        print(f"\n{name}: no records; skipped")
        return

    offsets = sorted(set([
        0,
        min(1_000, max(0, total - 1)),
        min(10_000, max(0, total - 1)),
        min(50_000, max(0, total - 1)),
        max(0, total - PAGE_SIZE),
    ]))

    print(f"\n{name} ({total:,} records)")
    print(f"{'Offset':>10} | {'Offset ms':>12} | {'Keyset ms':>12}")
    print("-" * 42)

    for offset in offsets:
        last_id = db.scalar(
            select(model.id)
            .order_by(model.id)
            .offset(offset)
            .limit(1)
        )

        if last_id is None:
            continue

        offset_ms = measure(
            lambda session: offset_query(session, model, offset)
        )

        keyset_ms = measure(
            lambda session: keyset_query(
                session, model, last_id - 1
            )
        )

        print(
            f"{offset:>10,} | "
            f"{offset_ms:>12.3f} | "
            f"{keyset_ms:>12.3f}"
        )


if __name__ == "__main__":
    with SessionLocal() as db:
        for name, model in MODELS:
            benchmark_table(db, name, model)
