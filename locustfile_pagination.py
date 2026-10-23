import random

from locust import HttpUser, between, task


class PaginationUser(HttpUser):
    wait_time = between(0.5, 1.5)

    @task(1)
    def courses_offset_deep_page(self):
        self.client.get(
            "/api/courses?skip=490000&limit=20",
            name="/api/courses (deep offset)",
        )

    @task(1)
    def courses_keyset(self):
        after_id = random.randint(400_000, 499_000)
        self.client.get(
            f"/api/courses?after_id={after_id}&limit=20",
            name="/api/courses (keyset)",
        )

    @task(1)
    def exams_offset_deep_page(self):
        self.client.get(
            "/api/exams?skip=490000&limit=20",
            name="/api/exams (deep offset)",
        )

    @task(1)
    def exams_keyset(self):
        after_id = random.randint(400_000, 499_000)
        self.client.get(
            f"/api/exams?after_id={after_id}&limit=20",
            name="/api/exams (keyset)",
        )
