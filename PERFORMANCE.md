# UniData API Performance Notes

## What I tested

I built this API to store and read university data. The test database contains about 1.01 million records across departments, lecturers, courses, and exams.

I used Locust to send requests to the API. I tested both SQLite and PostgreSQL. I also compared two ways of moving through large result sets:

- offset pagination, which skips rows before returning the requested page;
- keyset pagination, which uses `after_id` to continue from a known record.

The API uses synchronous FastAPI handlers and synchronous SQLAlchemy sessions.

## Database and connection settings

The PostgreSQL pool has:

- 10 base connections;
- up to 20 overflow connections;
- 30 checked-out connections at most;
- a 30-second pool timeout;
- connection pre-ping enabled.

The default AnyIO thread limiter is set to 30 tokens. This limits the number of synchronous request tasks that can run at the same time in one process.

When SQLAlchemy cannot get a connection before the pool timeout, the API returns HTTP 503 and sends `Retry-After: 1`. This gives the client a clear overload response. It does not increase the pool size or remove the underlying bottleneck.

## SQLite load results

These are the recorded SQLite results:

| Users | Requests | Throughput | Average | p95 | Failures |
|---:|---:|---:|---:|---:|---:|
| 10 | 97 | 5.2 RPS | 14.93 ms | 28 ms | 0 |
| 25 | 322 | 12.5 RPS | 12.94 ms | 38 ms | 0 |
| 50 | 2,336 | 25.6 RPS | 13.43 ms | 27 ms | 0 |
| 100 | 7,865 | 50.0 RPS | 15.97 ms | 38 ms | 0 |

The test lengths were not exactly the same, so these numbers are useful for a general comparison, but they are not a perfectly controlled experiment.

## PostgreSQL load results

These are the recorded PostgreSQL results:

| Users | Requests | Throughput | Average | p95 | Failures |
|---:|---:|---:|---:|---:|---:|
| 10 | 584 | 5.0 RPS | 12.84 ms | 19 ms | 0 |
| 25 | 1,471 | 12.5 RPS | 14.29 ms | 25 ms | 0 |
| 50 | 2,873 | 24.8 RPS | 16.94 ms | 38 ms | 0 |
| 100 | 5,525 | 50.9 RPS | 18.32 ms | 42 ms | 0 |

There is no recorded 150-user SQLite or PostgreSQL result.

A later 100-user PostgreSQL run recorded about 61 RPS, 380–400 ms average latency, about 1,000 ms p95 latency, and 0% failures. The exact test conditions were not recorded in the same format as the table above, so I do not compare the two 100-user results directly.

A later 200-user PostgreSQL run recorded:

| Users | Requests | Throughput | Average | Median | p95 | p99 | Failures |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 200 | 16,717 | 94.4 RPS | 96.57 ms | 33 ms | 530 ms | 860 ms | 0 |

This was one successful run. It does not prove that the API can always handle 200 users without errors. Other 200-user runs filled the connection pool and returned failures.

## Connection pool results at 200 users

One recorded comparison looked like this:

| Metric | Before | After |
|---|---:|---:|
| Concurrent users | 200 | 200 |
| Total requests | 3,939 | 21,532 |
| Failed requests | 275 | 39 |
| Average latency | 8,097.1 ms | 325.54 ms |
| p95 latency | 91,000 ms | 790 ms |
| Pool capacity | 15 | 30 |

The second run still had 39 failed requests. So the API should not be described as error-free at 200 concurrent users.

The main problem seen at high load was connection-pool exhaustion. Synchronous requests also compete for the AnyIO threadpool. When the system is busy, a request can wait for a thread and then wait again for a database connection.

## Offset and keyset pagination

The focused Locust test used 25 users. It made 661 requests and had no failures.

| Request type | Average | p95 |
|---|---:|---:|
| Courses – deep offset | 107.42 ms | 190 ms |
| Courses – keyset | 15.51 ms | 42 ms |
| Exams – deep offset | 107.52 ms | 220 ms |
| Exams – keyset | 17.27 ms | 84 ms |

I also ran a database-only test with 30 runs per query. Each query returned 20 records from around the 490,000th position.

| Query | Average | Median |
|---|---:|---:|
| Courses – offset | 82.321 ms | 79.841 ms |
| Courses – keyset | 0.708 ms | 0.333 ms |
| Exams – offset | 72.099 ms | 67.082 ms |
| Exams – keyset | 0.364 ms | 0.289 ms |

Keyset pagination was much faster for deep pages. The database-only results show why: offset queries must pass over many earlier rows, while keyset queries can start from the `id` value.

Offset pagination is still available for compatibility, but clients should use `after_id` when moving through large tables.

## What I learned

The API worked well at the lower recorded loads. The 50- and 100-user PostgreSQL tables show no failures in those runs.

At higher loads, the main limit was not just the SQL query speed. The SQLAlchemy pool and the synchronous threadpool could both become full. This led to long waits and failed requests.

The HTTP 503 response makes pool overload easier for clients to recognize than an HTTP 500. It is still a failure response and should be counted as such in load tests.

## Limitations

- A run with zero failures only describes that run. It does not show the maximum capacity of the API.
- The historical tests did not all use the same duration and exact Locust settings.
- The 200-user successful run and the 200-user failure runs show that results can change between runs under heavy load.
- Diagnostic Uvicorn logs help explain pool and threadpool behavior, but they are not a replacement for a Locust summary.
- I am not adding new benchmark numbers until Locust is run again with controlled and recorded settings.

**Tools:** FastAPI, PostgreSQL, SQLAlchemy, Locust, Python.
