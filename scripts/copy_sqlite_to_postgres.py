from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from app import models
from app.database import engine

SQLITE_URL = "sqlite:///./unidata.db"

sqlite_engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
)

SQLiteSession = sessionmaker(bind=sqlite_engine)
PostgresSession = sessionmaker(bind=engine)


def copy_table(source_session, target_session, model, batch_size=5000):
    total = source_session.scalar(
        select(func.count()).select_from(model)
    )
    print(f"Copying {model.__tablename__}: {total:,} records")

    last_id = 0
    copied = 0

    while True:
        rows = source_session.scalars(
            select(model)
            .where(model.id > last_id)
            .order_by(model.id)
            .limit(batch_size)
        ).all()

        if not rows:
            break

        records = [
            {
                column.name: getattr(row, column.name)
                for column in model.__table__.columns
            }
            for row in rows
        ]

        target_session.bulk_insert_mappings(model, records)
        target_session.commit()

        copied += len(records)
        last_id = records[-1]["id"]
        print(f"  Copied {copied:,}/{total:,}")

    print(f"Finished {model.__tablename__}")


def main():
    models_to_copy = [
        models.Department,
        models.Lecturer,
        models.Course,
        models.Exam,
    ]

    with SQLiteSession() as source, PostgresSession() as target:
        for model in models_to_copy:
            copy_table(source, target, model)

    print("\nData copy completed.")


if __name__ == "__main__":
    main()
