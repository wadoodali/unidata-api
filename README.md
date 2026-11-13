# UniData API

UniData API is a university information API that I built with FastAPI and SQLAlchemy. It manages departments, lecturers, courses, and exams.

The project uses synchronous SQLAlchemy sessions with PostgreSQL. It also includes SQLite support, automated API tests, Locust load tests, and small scripts for checking database performance.

## Dataset and database setup

The recorded tests use about 1.01 million records.

For PostgreSQL, the connection pool is configured with:

- 10 normal connections;
- up to 20 extra connections when the pool is busy;
- a maximum of 30 checked-out connections;
- a 30-second pool timeout;
- connection pre-ping enabled.

Synchronous request work is limited to 30 AnyIO thread tokens. In simple terms, this limits how many synchronous requests can run at the same time in one process.

## What I tested

I tested the API with SQLite and PostgreSQL. I also compared normal offset pagination with keyset pagination. Keyset pagination uses an `after_id` value to continue from a previous record instead of skipping a large number of rows.

The recorded PostgreSQL results include:

- 50 users: 2,873 requests, 24.8 RPS, 16.94 ms average, 38 ms p95, 0 failures.
- 100 users: 5,525 requests, 50.9 RPS, 18.32 ms average, 42 ms p95, 0 failures.
- A later 200-user run: 16,717 requests, 94.4 RPS, 96.57 ms average, 33 ms median, 530 ms p95, 860 ms p99, 0 failures.

Other 200-user runs filled the 30-connection pool and had failures. Because of that, I cannot say that the API handles 200 concurrent users without errors. There is no recorded 150-user result.

Deep offset pagination was much slower than keyset pagination. In the focused test, deep course and exam offset requests took about 107 ms on average. The keyset requests took about 16–17 ms.

When the SQLAlchemy pool times out, the API returns HTTP 503 with a short error message and a `Retry-After: 1` header. This is clearer than returning an HTTP 500, but it does not create more capacity or fix pool and threadpool saturation.

More details and all recorded tables are in [PERFORMANCE.md](PERFORMANCE.md).
