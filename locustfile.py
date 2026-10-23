import random

from locust import HttpUser, between, task


class UniDataUser(HttpUser):
    # Wait 1–3 seconds between tasks to simulate user think time.
    wait_time = between(1, 3)

    def on_start(self):
        self.course_id = random.randint(1, 500_000)
        self.exam_id = random.randint(1, 500_000)
        self.department_id = random.randint(1, 1_000)
        self.lecturer_id = random.randint(1, 10_000)

    @task(5)
    def list_courses(self):
        self.client.get(
            "/api/courses?limit=20",
            name="/api/courses",
        )

    @task(3)
    def list_exams(self):
        self.client.get(
            "/api/exams?limit=20",
            name="/api/exams",
        )

    @task(2)
    def get_course(self):
        self.client.get(
            f"/api/courses/{self.course_id}",
            name="/api/courses/[course_id]",
        )

    @task(2)
    def get_exam(self):
        self.client.get(
            f"/api/exams/{self.exam_id}",
            name="/api/exams/[exam_id]",
        )

    @task(1)
    def list_departments(self):
        self.client.get(
            "/api/departments?limit=20",
            name="/api/departments",
        )

    @task(1)
    def list_lecturers(self):
        self.client.get(
            "/api/lecturers?limit=20",
            name="/api/lecturers",
        )

    @task(2)
    def paginate_courses(self):
        after_id = random.randint(1, 499_000)
        self.client.get(
            f"/api/courses?after_id={after_id}&limit=20",
            name="/api/courses?after_id=[id]",
        )

    @task(2)
    def paginate_exams(self):
        after_id = random.randint(1, 499_000)
        self.client.get(
            f"/api/exams?after_id={after_id}&limit=20",
            name="/api/exams?after_id=[id]",
        )
