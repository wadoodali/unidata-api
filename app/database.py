
import contextvars
import os
import time
import logging

from sqlalchemy import create_engine, event
from sqlalchemy.exc import TimeoutError as SQLAlchemyTimeoutError
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./unidata.db")


# Configure database logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("database_timing")


# Request ID tracking
request_id_context = contextvars.ContextVar(
    "request_id",
    default=None,
)


# Database connection configuration
connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}


engine_options = {
    "connect_args": connect_args,
}


# PostgreSQL connection pool configuration
if DATABASE_URL.startswith("postgresql"):
    engine_options.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
        "pool_pre_ping": True,
    })


engine = create_engine(
    DATABASE_URL,
    **engine_options,
)


# Enable foreign key constraints for SQLite
if DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Measure database connection checkout
@event.listens_for(engine, "checkout")
def connection_checkout(
    dbapi_connection,
    connection_record,
    connection_proxy,
):
    request_id = request_id_context.get()

    connection_record.info["checkout_time"] = time.perf_counter()
    connection_record.info["request_id"] = request_id

    logger.info(
        "DB CONNECTION CHECKOUT request_id=%s pool_status=%s",
        request_id or "-",
        engine.pool.status(),
    )


# Measure database connection check-in
@event.listens_for(engine, "checkin")
def connection_checkin(dbapi_connection, connection_record):
    checkout_time = connection_record.info.pop(
        "checkout_time",
        None,
    )

    request_id = connection_record.info.pop(
        "request_id",
        None,
    )

    if checkout_time is not None:
        duration = time.perf_counter() - checkout_time

        logger.info(
            "DB CONNECTION CHECKIN request_id=%s hold_duration=%.3f "
            "pool_status=%s",
            request_id or "-",
            duration,
            engine.pool.status(),
        )


# Database session configuration
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


Base = declarative_base()


# Database dependency for FastAPI
def get_db():
    db = SessionLocal()

    try:
        yield db

    except SQLAlchemyTimeoutError:
        logger.exception(
            "DB CONNECTION ACQUISITION TIMEOUT request_id=%s "
            "pool_status=%s",
            request_id_context.get() or "-",
            engine.pool.status(),
        )
        raise

    finally:
        db.close()
