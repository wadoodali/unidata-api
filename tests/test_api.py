import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.exc import TimeoutError as SQLAlchemyTimeoutError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db


# Create a separate in-memory database for tests.
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(test_engine, "connect")
def enable_test_foreign_keys(connection, record):
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=test_engine)


# Helper functions for creating test records.

def create_department(client, name="Computer Science"):
    response = client.post(
        "/api/departments",
        json={"name": name},
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_lecturer(
    client,
    department_id,
    name="Test Lecturer",
    email="lecturer@example.com",
):
    response = client.post(
        "/api/lecturers",
        json={
            "name": name,
            "email": email,
            "department_id": department_id,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_course(
    client,
    department_id,
    lecturer_id,
    code="CS101",
    title="Introduction to Computing",
):
    response = client.post(
        "/api/courses",
        json={
            "course_code": code,
            "title": title,
            "ects": 5,
            "department_id": department_id,
            "lecturer_id": lecturer_id,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_exam(client, course_id):
    response = client.post(
        "/api/exams",
        json={
            "course_id": course_id,
            "exam_date": "2027-01-20T09:00:00",
            "room": "A101",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


# ROOT ENDPOINT

def test_root_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to UniData API"
    }


# DEPARTMENT TESTS

def test_list_departments(client):
    response = client.get("/api/departments")

    assert response.status_code == 200
    assert response.json() == []


def test_create_department(client):
    response = client.post(
        "/api/departments",
        json={"name": "Computer Science"},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Computer Science"
    assert isinstance(response.json()["id"], int)


def test_create_department_without_name(client):
    response = client.post("/api/departments", json={})

    assert response.status_code == 422


def test_create_department_with_empty_name(client):
    response = client.post(
        "/api/departments",
        json={"name": ""},
    )

    assert response.status_code == 422


def test_create_duplicate_department(client):
    create_department(client)

    response = client.post(
        "/api/departments",
        json={"name": "Computer Science"},
    )

    assert response.status_code == 409


def test_get_department(client):
    department = create_department(client)

    response = client.get(
        f"/api/departments/{department['id']}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == department["id"]


def test_get_missing_department(client):
    response = client.get("/api/departments/9999")

    assert response.status_code == 404


def test_update_department(client):
    department = create_department(client)

    response = client.patch(
        f"/api/departments/{department['id']}",
        json={"name": "Software Engineering"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Software Engineering"


def test_update_missing_department(client):
    response = client.patch(
        "/api/departments/9999",
        json={"name": "New Department"},
    )

    assert response.status_code == 404


def test_delete_department(client):
    department = create_department(client)

    response = client.delete(
        f"/api/departments/{department['id']}"
    )

    assert response.status_code in (200, 204)
    assert client.get(
        f"/api/departments/{department['id']}"
    ).status_code == 404


def test_delete_missing_department(client):
    response = client.delete("/api/departments/9999")

    assert response.status_code == 404


# LECTURER TESTS

def test_list_lecturers(client):
    response = client.get("/api/lecturers")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_lecturer(client):
    department = create_department(client)
    lecturer = create_lecturer(client, department["id"])

    assert lecturer["name"] == "Test Lecturer"
    assert lecturer["email"] == "lecturer@example.com"
    assert isinstance(lecturer["id"], int)


def test_create_lecturer_with_invalid_department(client):
    response = client.post(
        "/api/lecturers",
        json={
            "name": "Test Lecturer",
            "email": "lecturer@example.com",
            "department_id": 9999,
        },
    )

    # Matches the current API behavior.
    assert response.status_code == 422


def test_create_duplicate_lecturer_email(client):
    department = create_department(client)
    create_lecturer(client, department["id"])

    response = client.post(
        "/api/lecturers",
        json={
            "name": "Another Lecturer",
            "email": "lecturer@example.com",
            "department_id": department["id"],
        },
    )

    assert response.status_code == 409


def test_get_lecturer(client):
    department = create_department(client)
    lecturer = create_lecturer(client, department["id"])

    response = client.get(
        f"/api/lecturers/{lecturer['id']}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == lecturer["id"]


def test_get_missing_lecturer(client):
    response = client.get("/api/lecturers/9999")

    assert response.status_code == 404


def test_update_lecturer(client):
    department = create_department(client)
    lecturer = create_lecturer(client, department["id"])

    response = client.patch(
        f"/api/lecturers/{lecturer['id']}",
        json={"name": "Updated Lecturer"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Lecturer"


def test_delete_lecturer(client):
    department = create_department(client)
    lecturer = create_lecturer(client, department["id"])

    response = client.delete(
        f"/api/lecturers/{lecturer['id']}"
    )

    assert response.status_code in (200, 204)
    assert client.get(
        f"/api/lecturers/{lecturer['id']}"
    ).status_code == 404


# COURSE TESTS

def test_list_courses(client):
    response = client.get("/api/courses")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_course(client):
    department = create_department(client)
    lecturer = create_lecturer(client, department["id"])

    course = create_course(
        client,
        department["id"],
        lecturer["id"],
    )

    assert course["course_code"] == "CS101"
    assert course["title"] == "Introduction to Computing"
    assert course["ects"] == 5
    assert isinstance(course["id"], int)


def test_create_course_with_invalid_department(client):
    department = create_department(client)
    lecturer = create_lecturer(client, department["id"])

    response = client.post(
        "/api/courses",
        json={
            "course_code": "CS102",
            "title": "Algorithms",
            "ects": 5,
            "department_id": 9999,
            "lecturer_id": lecturer["id"],
        },
    )

    assert response.status_code == 422


def test_create_course_with_invalid_lecturer(client):
    department = create_department(client)

    response = client.post(
        "/api/courses",
        json={
            "course_code": "CS102",
            "title": "Algorithms",
            "ects": 5,
            "department_id": department["id"],
            "lecturer_id": 9999,
        },
    )

    assert response.status_code == 422


def test_create_duplicate_course_code(client):
    department = create_department(client)
    lecturer = create_lecturer(client, department["id"])

    create_course(
        client,
        department["id"],
        lecturer["id"],
    )

    response = client.post(
        "/api/courses",
        json={
            "course_code": "CS101",
            "title": "Another Course",
            "ects": 5,
            "department_id": department["id"],
            "lecturer_id": lecturer["id"],
        },
    )

    assert response.status_code == 409


def test_get_course(client):
    department = create_department(client)
    lecturer = create_lecturer(client, department["id"])
    course = create_course(
        client,
        department["id"],
        lecturer["id"],
    )

    response = client.get(f"/api/courses/{course['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == course["id"]


def test_get_missing_course(client):
    response = client.get("/api/courses/9999")

    assert response.status_code == 404


def test_update_course(client):
    department = create_department(client)
    lecturer = create_lecturer(client, department["id"])
    course = create_course(
        client,
        department["id"],
        lecturer["id"],
    )

    response = client.patch(
        f"/api/courses/{course['id']}",
        json={"title": "Updated Course Title"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated Course Title"


def test_delete_course(client):
    department = create_department(client)
    lecturer = create_lecturer(client, department["id"])
    course = create_course(
        client,
        department["id"],
        lecturer["id"],
    )

    response = client.delete(f"/api/courses/{course['id']}")

    assert response.status_code in (200, 204)
    assert client.get(
        f"/api/courses/{course['id']}"
    ).status_code == 404



def test_get_courses_with_after_id(client):
    department = create_department(client)
    lecturer = create_lecturer(client, department["id"])

    first_course = create_course(
        client,
        department["id"],
        lecturer["id"],
        code="CS101",
    )
    second_course = create_course(
        client,
        department["id"],
        lecturer["id"],
        code="CS102",
    )

    response = client.get(
        f"/api/courses?after_id={first_course['id']}&limit=20"
    )

    assert response.status_code == 200
    returned_ids = [course["id"] for course in response.json()]
    assert first_course["id"] not in returned_ids
    assert second_course["id"] in returned_ids


# EXAM TESTS

def test_list_exams(client):
    response = client.get("/api/exams")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_exam(client):
    department = create_department(client)
    lecturer = create_lecturer(client, department["id"])
    course = create_course(
        client,
        department["id"],
        lecturer["id"],
    )

    exam = create_exam(client, course["id"])

    assert exam["course_id"] == course["id"]
    assert exam["room"] == "A101"
    assert isinstance(exam["id"], int)


def test_create_exam_with_invalid_course(client):
    response = client.post(
        "/api/exams",
        json={
            "course_id": 9999,
            "exam_date": "2027-01-20T09:00:00",
            "room": "A101",
        },
    )

    assert response.status_code == 422


def test_create_exam_without_required_fields(client):
    response = client.post("/api/exams", json={})

    assert response.status_code == 422


def test_get_exam(client):
    department = create_department(client)
    lecturer = create_lecturer(client, department["id"])
    course = create_course(
        client,
        department["id"],
        lecturer["id"],
    )
    exam = create_exam(client, course["id"])

    response = client.get(f"/api/exams/{exam['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == exam["id"]


def test_get_missing_exam(client):
    response = client.get("/api/exams/9999")

    assert response.status_code == 404


def test_update_exam(client):
    department = create_department(client)
    lecturer = create_lecturer(client, department["id"])
    course = create_course(
        client,
        department["id"],
        lecturer["id"],
    )
    exam = create_exam(client, course["id"])

    response = client.patch(
        f"/api/exams/{exam['id']}",
        json={"room": "B202"},
    )

    assert response.status_code == 200
    assert response.json()["room"] == "B202"


def test_delete_exam(client):
    department = create_department(client)
    lecturer = create_lecturer(client, department["id"])
    course = create_course(
        client,
        department["id"],
        lecturer["id"],
    )
    exam = create_exam(client, course["id"])

    response = client.delete(f"/api/exams/{exam['id']}")

    assert response.status_code in (200, 204)
    assert client.get(
        f"/api/exams/{exam['id']}"
    ).status_code == 404


def test_keyset_pagination_for_all_list_endpoints(client):
    department_one = create_department(client, name="Department One")
    department_two = create_department(client, name="Department Two")
    lecturer_one = create_lecturer(
        client,
        department_one["id"],
        email="one@example.com",
    )
    lecturer_two = create_lecturer(
        client,
        department_one["id"],
        name="Second Lecturer",
        email="two@example.com",
    )
    course_one = create_course(
        client,
        department_one["id"],
        lecturer_one["id"],
        code="CS201",
    )
    course_two = create_course(
        client,
        department_two["id"],
        lecturer_two["id"],
        code="CS202",
    )
    exam_one = create_exam(client, course_one["id"])
    exam_two = create_exam(client, course_two["id"])

    cases = [
        ("departments", department_one["id"], department_two["id"]),
        ("lecturers", lecturer_one["id"], lecturer_two["id"]),
        ("courses", course_one["id"], course_two["id"]),
        ("exams", exam_one["id"], exam_two["id"]),
    ]

    for resource, first_id, second_id in cases:
        first_page = client.get(f"/api/{resource}?limit=1")
        assert first_page.status_code == 200
        assert len(first_page.json()) == 1

        next_page = client.get(
            f"/api/{resource}?after_id={first_id}&limit=20"
        )
        assert next_page.status_code == 200
        next_ids = [item["id"] for item in next_page.json()]
        assert first_id not in next_ids
        assert second_id in next_ids

        empty_page = client.get(
            f"/api/{resource}?after_id={second_id}&limit=20"
        )
        assert empty_page.status_code == 200
        assert empty_page.json() == []


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/departments",
        "/api/lecturers",
        "/api/courses",
        "/api/exams",
    ],
)
@pytest.mark.parametrize("limit", [0, 101])
def test_list_endpoints_reject_invalid_limits(client, endpoint, limit):
    response = client.get(f"{endpoint}?limit={limit}")

    assert response.status_code == 422


def test_sqlalchemy_timeout_returns_503(client):
    def timeout_get_db():
        raise SQLAlchemyTimeoutError("simulated pool timeout")

    original_override = app.dependency_overrides[get_db]
    app.dependency_overrides[get_db] = timeout_get_db

    try:
        response = client.get("/api/departments")
    finally:
        app.dependency_overrides[get_db] = original_override

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Database temporarily unavailable. Please retry later."
    }
    assert response.headers["retry-after"] == "1"
