# UniData API Performance Notes

See [README.md](README.md) for setup, application startup, test, and Locust commands.

## Test setup

The recorded tests used about 1.01 million records across departments, lecturers, courses, and exams.

The API uses synchronous FastAPI handlers and synchronous SQLAlchemy sessions. PostgreSQL was configured with:

- 10 base pool connections;
- up to 20 overflow connections;
- 30 checked-out connections at most;
- a 30-second pool timeout;
- connection pre-ping enabled.

The AnyIO thread limiter is set to 30 tokens.

The application returns HTTP 503 with `Retry-After: 1` when SQLAlchemy cannot obtain a pool connection before the timeout. A 503 is a failed/overload response, not a successful request.

## API-level load tests

The API-level tests used Locust. The normal workload is in `locustfile.py`:

- users wait randomly between 1 and 3 seconds between tasks;
- tasks cover list, lookup, and keyset-pagination requests for all main resources;
- each list request uses `limit=20`.

The pagination workload is in `locustfile_pagination.py`:

- users wait randomly between 0.5 and 1.5 seconds;
- it compares `skip=490000` with keyset requests using random `after_id` values between 400,000 and 499,000;
- page size is 20.

The historical records do not contain the exact Locust spawn rate and duration for every run. The tables below therefore preserve the measurements, but runs with different conditions should not be compared as a controlled experiment.

### SQLite results

| Users | Requests | Throughput | Average | p95 | Failures |
|---:|---:|---:|---:|---:|---:|
| 10 | 97 | 5.2 RPS | 14.93 ms | 28 ms | 0 |
| 25 | 322 | 12.5 RPS | 12.94 ms | 38 ms | 0 |
| 50 | 2,336 | 25.6 RPS | 13.43 ms | 27 ms | 0 |
| 100 | 7,865 | 50.0 RPS | 15.97 ms | 38 ms | 0 |

The database backend was SQLite. The test lengths were not exactly the same.

### PostgreSQL results

| Users | Requests | Throughput | Average | p95 | Failures |
|---:|---:|---:|---:|---:|---:|
| 10 | 584 | 5.0 RPS | 12.84 ms | 19 ms | 0 |
| 25 | 1,471 | 12.5 RPS | 14.29 ms | 25 ms | 0 |
| 50 | 2,873 | 24.8 RPS | 16.94 ms | 38 ms | 0 |
| 100 | 5,525 | 50.9 RPS | 18.32 ms | 42 ms | 0 |

The database backend was PostgreSQL. There is no recorded 150-user SQLite or PostgreSQL result.

A later 100-user PostgreSQL run recorded about 61 RPS, 380–400 ms average latency, about 1,000 ms p95 latency, and 0% failures. Its exact Locust duration and spawn rate were not recorded in the project, so it is not directly comparable with the table above.

A later successful 200-user PostgreSQL run recorded:

| Users | Requests | Throughput | Average | Median | p95 | p99 | Failures |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 200 | 16,717 | 94.4 RPS | 96.57 ms | 33 ms | 530 ms | 860 ms | 0 |

This means that run had no recorded failed requests. It does not prove that the API always handles 200 users without errors. Other 200-user runs filled the 30-connection pool and returned failures, including HTTP 503 responses after overload handling was added.

### Recorded 200-user pool comparison

One recorded comparison was:

| Metric | Before | After |
|---|---:|---:|
| Concurrent users | 200 | 200 |
| Total requests | 3,939 | 21,532 |
| Failed requests | 275 | 39 |
| Average latency | 8,097.1 ms | 325.54 ms |
| p95 latency | 91,000 ms | 790 ms |
| Pool capacity | 15 | 30 |

The `After` run still had 39 failed requests. It should not be presented as an error-free 200-user result.

The main bottleneck seen at high load was connection-pool exhaustion, with synchronous request work also competing for the AnyIO thread limiter. Requests could wait for a thread and then wait for a database connection.

## Database-only pagination benchmarks

These tests do not send HTTP requests. They measure database queries through the SQLAlchemy engine configured in `app.database`.

### `scripts/benchmark_report.py`

The script can be run with:

```powershell
python scripts/benchmark_report.py
```

Its verified settings are:

- 30 timed runs per query;
- one warm-up query per case;
- page size 20;
- offset and `after_id` value 490,000;
- courses and exams only.

Recorded results:

| Query | Average | Median |
|---|---:|---:|
| Courses – offset | 82.321 ms | 79.841 ms |
| Courses – keyset | 0.708 ms | 0.333 ms |
| Exams – offset | 72.099 ms | 67.082 ms |
| Exams – keyset | 0.364 ms | 0.289 ms |

### `scripts/benchmark_pagination.py`

The script can be run with:

```powershell
python scripts/benchmark_pagination.py
```

Its verified settings are:

- 10 timed runs per query;
- one warm-up query per case;
- page size 20;
- departments, lecturers, courses, and exams;
- offsets of 0, up to 1,000, up to 10,000, up to 50,000, and the final page where available.

This script prints mean timings for each table and offset. Its output is separate from the recorded Locust results above.

## Offset versus keyset pagination

The focused Locust comparison used 25 users. The project records 661 requests and no failures for this test. The exact spawn rate and duration were not recorded.

| Request type | Average | p95 |
|---|---:|---:|
| Courses – deep offset | 107.42 ms | 190 ms |
| Courses – keyset | 15.51 ms | 42 ms |
| Exams – deep offset | 107.52 ms | 220 ms |
| Exams – keyset | 17.27 ms | 84 ms |

The keyset requests were much faster at deep positions. The database-only results show the same pattern because offset queries must pass over earlier rows, while keyset queries can start from the `id` value.

Offset pagination remains available for compatibility. Clients moving through large tables should use `after_id`.

## Conclusions and limitations

- The lower-load PostgreSQL table shows 0 failures at 50 and 100 users in those recorded runs.
- One 200-user run had 0 failures, but other 200-user runs had failures after the connection pool filled.
- HTTP 503 responses are counted as failures/overload responses, not successful requests.
- The measurements were made under different historical conditions, so they are not all directly comparable.
- The database-only benchmarks do not include HTTP handling, AnyIO scheduling, response serialization, or Locust timing.
- The Locust scripts define the request mix and user wait times, but the historical spawn rates and durations were not recorded consistently.
- No result here should be treated as a maximum-capacity claim.
