
import platform
import statistics
import time

from sqlalchemy import text

from app.database import engine


RUNS = 30
PAGE_SIZE = 20
OFFSET = 490_000
AFTER_ID = 490_000

QUERIES = {
    "Courses offset": (
        "SELECT * FROM courses ORDER BY id LIMIT :limit OFFSET :offset",
        {"limit": PAGE_SIZE, "offset": OFFSET},
    ),
    "Courses keyset": (
        "SELECT * FROM courses WHERE id > :after_id ORDER BY id LIMIT :limit",
        {"limit": PAGE_SIZE, "after_id": AFTER_ID},
    ),
    "Exams offset": (
        "SELECT * FROM exams ORDER BY id LIMIT :limit OFFSET :offset",
        {"limit": PAGE_SIZE, "offset": OFFSET},
    ),
    "Exams keyset": (
        "SELECT * FROM exams WHERE id > :after_id ORDER BY id LIMIT :limit",
        {"limit": PAGE_SIZE, "after_id": AFTER_ID},
    ),
}


def measure(connection, query, params):
    connection.execute(text(query), params).fetchall()  # Warm-up
    timings = []

    for _ in range(RUNS):
        start = time.perf_counter()
        connection.execute(text(query), params).fetchall()
        timings.append((time.perf_counter() - start) * 1000)

    return statistics.mean(timings), statistics.median(timings)


def main():
    results = {}

    print(f"Python: {platform.python_version()}")
    print(f"Runs per query: {RUNS}")
    print(f"Page size: {PAGE_SIZE}")
    print(f"Offset / after_id: {OFFSET}")
    print("\nDatabase-only pagination benchmark")
    print("-" * 76)

    with engine.connect() as connection:
        for name, (query, params) in QUERIES.items():
            mean_ms, median_ms = measure(connection, query, params)
            results[name] = mean_ms

            print(
                f"{name:20} "
                f"mean={mean_ms:9.3f} ms  "
                f"median={median_ms:9.3f} ms"
            )

    print("\nMean-time comparison")
    for table in ("Courses", "Exams"):
        offset_ms = results[f"{table} offset"]
        keyset_ms = results[f"{table} keyset"]
        speedup = offset_ms / keyset_ms if keyset_ms else float("inf")
        improvement = (
            (offset_ms - keyset_ms) / offset_ms * 100
            if offset_ms else 0
        )

        print(
            f"{table}: {speedup:.1f}x speedup, "
            f"{improvement:.1f}% lower mean time with keyset"
        )


if __name__ == "__main__":
    main()
