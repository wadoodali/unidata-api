# UniData API – Performance Testing

## 1. What I tested

I wanted to find out how well the UniData API performs with a large amount of data and multiple users making requests at the same time.

The database contains around 1 million records across departments, lecturers, courses and exams. I used Locust to test the API under different user loads and also compared two pagination methods: offset pagination and keyset pagination.

## 2. Load testing with Locust

I tested the API with 10, 25, 50 and 100 simulated users. I looked at throughput, response time, latency at the 95th percentile (p95), and failed requests.

### Results

| Simulated users | Requests completed | Throughput (RPS) | Average response time | p95 response time | Failures |
|---:|---:|---:|---:|---:|---:|
| 10 | 97 | 5.2 | 14.93 ms | 28 ms | 0 |
| 25 | 322 | 12.5 | 12.94 ms | 38 ms | 0 |
| 50 | 2,336 | 25.6 | 13.43 ms | 27 ms | 0 |
| 100 | 7,865 | 50.0 | 15.97 ms | 38 ms | 0 |

*Note: The test durations varied, so these results are useful for understanding general performance but are not a perfectly controlled comparison.*

### What the results mean

As the number of simulated users increased, throughput also increased. At 100 users, the API handled around 50 requests per second, with an average response time of about 16 ms.

The p95 result at 100 users was 38 ms. This means that 95% of requests completed in 38 ms or less during that test.

There were no failed requests in the recorded tests, which is a good sign. However, these results do not mean the API can handle unlimited traffic. More testing would be needed to find its maximum capacity.

## 3. Comparing pagination methods

I also used Locust to compare deep offset pagination with keyset pagination for courses and exams.

The focused test used 25 simulated users.

| Request type | Average response time | p95 response time |
|---|---:|---:|
| Courses – deep offset | 107.42 ms | 190 ms |
| Courses – keyset | 15.51 ms | 42 ms |
| Exams – deep offset | 107.52 ms | 220 ms |
| Exams – keyset | 17.27 ms | 84 ms |

There were 661 requests in total and no failures during this test.

### What I found

Offset pagination was much slower when accessing deep pages. The average response time was around 107 ms for both courses and exams, while keyset pagination returned responses in around 16–17 ms on average.

This suggests that keyset pagination is a better choice when clients need to navigate large datasets.

The results are not a perfect like-for-like comparison because the offset requests used a fixed offset, while the keyset requests used randomly selected IDs. Even so, the difference was large enough to justify further testing.

## 4. Database-level benchmark

To look more closely at the database itself, I ran a separate benchmark with 30 runs per query. Each query returned 20 records from around the 490,000th position.

| Query | Average time | Median time |
|---|---:|---:|
| Courses – offset | 82.321 ms | 79.841 ms |
| Courses – keyset | 0.708 ms | 0.333 ms |
| Exams – offset | 72.099 ms | 67.082 ms |
| Exams – keyset | 0.364 ms | 0.289 ms |

Keyset pagination was around 116 times faster for courses and 198 times faster for exams in this database-level test.

The reason is that offset pagination has to pass over earlier records, while keyset pagination uses the record ID to find the next set of records more directly.

These measurements only cover database queries and fetching results. They do not include the full API request and response process.

## 5. Conclusion

The load tests showed that the API handled the tested workloads without any recorded failures, and throughput increased as more simulated users were added.

The pagination tests also revealed a clear performance issue with deep offset queries. Switching to keyset pagination significantly reduced response times in both the API-level and database-level benchmarks.

The next step is to continue checking performance under controlled workloads and then compare SQLite with PostgreSQL using the same dataset and tests.
