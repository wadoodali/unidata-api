# UniData API

UniData API is a university information API built with FastAPI and SQLAlchemy. It manages departments, lecturers, courses, and exams.

The project uses synchronous SQLAlchemy sessions. It supports SQLite for local work and PostgreSQL for the larger performance tests. It also includes API tests, Locust load tests, data-generation tools, and database pagination benchmarks.

## Technical highlights

- CRUD endpoints for four university resources.
- PostgreSQL connection pooling with 10 base connections and 20 overflow connections.
- Function-scoped database dependencies.
- Bounded list endpoints with `limit` up to 100.
- Keyset pagination with `after_id` for large tables.
- HTTP 503 responses when the SQLAlchemy pool is exhausted.
- 48 automated API tests.
- A recorded test dataset of about 1.01 million records.

## Architecture

```text
HTTP request
    ↓
FastAPI route
    ↓
get_db() dependency
    ↓
SQLAlchemy Session
    ↓
QueuePool (PostgreSQL) or SQLite pool
    ↓
PostgreSQL / SQLite
```

Each database-backed request receives its own SQLAlchemy session. The routes use function-scoped dependencies, so the dependency cleanup runs after the route function and releases database resources before response finalization.

The application uses synchronous route handlers and synchronous SQLAlchemy. The AnyIO thread limiter is set to 30 tokens, while the PostgreSQL pool allows up to 30 checked-out connections. These two limits control how much database work one application process can handle at the same time.

## Setup

Create and activate a virtual environment, then install the existing pinned dependencies:

```powershell
python -m pip install -r requirements.txt
```

If `DATABASE_URL` is not set, the application uses the local SQLite database URL:

```text
sqlite:///./unidata.db
```

For PostgreSQL, set `DATABASE_URL` using the normal PostgreSQL SQLAlchemy URL format. Do not commit credentials or put passwords in this file.

The application calls SQLAlchemy `Base.metadata.create_all()` during startup. This project does not currently include a migration system.

## Run the API and tests

Start the API locally:

```powershell
python -m uvicorn app.main:app --reload
```

Run the tests:

```powershell
python -m pytest -q
```

The test suite uses a separate in-memory SQLite database. It does not replace PostgreSQL load or query-plan testing.

## Example requests

```powershell
curl http://127.0.0.1:8000/
curl "http://127.0.0.1:8000/api/courses?limit=20"
curl "http://127.0.0.1:8000/api/courses?after_id=100&limit=20"
curl -X POST http://127.0.0.1:8000/api/departments `
  -H "Content-Type: application/json" `
  -d '{"name":"Computer Science"}'
```

List endpoints also exist for departments, lecturers, and exams. The `after_id` form is preferred when moving through large tables because it avoids deep offset scans.

## Locust and database benchmarks

Start the normal Locust workload:

```powershell
locust -f locustfile.py --host http://127.0.0.1:8000
```

Start the pagination comparison workload:

```powershell
locust -f locustfile_pagination.py --host http://127.0.0.1:8000
```

The normal workload waits 1–3 seconds between tasks. The pagination workload waits 0.5–1.5 seconds. Historical user counts, spawn rates, and durations were not recorded consistently for every run, so the reported results should not be treated as perfectly comparable.

Database-only benchmarks can be run with:

```powershell
python scripts/benchmark_report.py
python scripts/benchmark_pagination.py
```

These scripts use the database configured through `app.database`. `benchmark_report.py` runs 30 timed queries per case at offset/`after_id` 490,000 with page size 20. `benchmark_pagination.py` runs 10 measurements across several offsets and all four tables.

## What I learned

The most useful result was the pagination comparison. Keyset queries stayed fast at deep positions, while offset queries became much slower.

The main limit at high concurrency was not only SQL execution. Synchronous request work, the AnyIO thread limiter, and the SQLAlchemy connection pool can all become full. When the pool times out, the API returns HTTP 503 with `Retry-After: 1`. That makes overload clear to clients, but it does not create more capacity.

See [PERFORMANCE.md](PERFORMANCE.md) for the recorded measurements, test conditions, and limitations.
