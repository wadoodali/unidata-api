from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="UniData API",
    description="A university information management API.",
    version="0.1.0",
)


def handle_integrity_error(db: Session, exc: IntegrityError):
    db.rollback()
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="The operation conflicts with existing database records or constraints.",
    ) from exc


def validate_patch(updates: dict):
    if any(value is None for value in updates.values()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Fields cannot be explicitly set to null.",
        )


@app.get("/")
def root():
    return {"message": "Welcome to UniData API"}


# -------------------------
# Departments
# -------------------------

@app.post(
    "/api/departments",
    response_model=schemas.DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_department(
    department: schemas.DepartmentCreate,
    db: Session = Depends(get_db),
):
    try:
        return crud.create_department(db, department)
    except IntegrityError as exc:
        handle_integrity_error(db, exc)


@app.get("/api/departments", response_model=list[schemas.DepartmentResponse])
def read_departments(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return crud.get_departments(db, skip, limit)


@app.get(
    "/api/departments/{department_id}",
    response_model=schemas.DepartmentResponse,
)
def read_department(
    department_id: int,
    db: Session = Depends(get_db),
):
    department = crud.get_department(db, department_id)
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found.")
    return department


@app.patch(
    "/api/departments/{department_id}",
    response_model=schemas.DepartmentResponse,
)
def update_department(
    department_id: int,
    updates: schemas.DepartmentUpdate,
    db: Session = Depends(get_db),
):
    try:
        department = crud.update_department(
            db, department_id, updates.model_dump(exclude_unset=True)
        )
        if department is None:
            raise HTTPException(status_code=404, detail="Department not found.")
        return department
    except IntegrityError as exc:
        handle_integrity_error(db, exc)


@app.delete("/api/departments/{department_id}", status_code=204)
def delete_department(department_id: int, db: Session = Depends(get_db)):
    try:
        if not crud.delete_department(db, department_id):
            raise HTTPException(status_code=404, detail="Department not found.")
    except IntegrityError as exc:
        handle_integrity_error(db, exc)


# -------------------------
# Lecturers
# -------------------------

@app.post(
    "/api/lecturers",
    response_model=schemas.LecturerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_lecturer(
    lecturer: schemas.LecturerCreate,
    db: Session = Depends(get_db),
):
    try:
        if crud.get_department(db, lecturer.department_id) is None:
            raise HTTPException(status_code=422, detail="Department not found.")
        return crud.create_lecturer(db, lecturer)
    except IntegrityError as exc:
        handle_integrity_error(db, exc)


@app.get("/api/lecturers", response_model=list[schemas.LecturerResponse])
def read_lecturers(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return crud.get_lecturers(db, skip, limit)


@app.get(
    "/api/lecturers/{lecturer_id}",
    response_model=schemas.LecturerResponse,
)
def read_lecturer(lecturer_id: int, db: Session = Depends(get_db)):
    lecturer = crud.get_lecturer(db, lecturer_id)
    if lecturer is None:
        raise HTTPException(status_code=404, detail="Lecturer not found.")
    return lecturer


@app.patch(
    "/api/lecturers/{lecturer_id}",
    response_model=schemas.LecturerResponse,
)
def update_lecturer(
    lecturer_id: int,
    updates: schemas.LecturerUpdate,
    db: Session = Depends(get_db),
):
    try:
        data = updates.model_dump(exclude_unset=True)
        validate_patch(data)
        if "department_id" in data and crud.get_department(db, data["department_id"]) is None:
            raise HTTPException(status_code=422, detail="Department not found.")
        lecturer = crud.update_lecturer(db, lecturer_id, data)
        if lecturer is None:
            raise HTTPException(status_code=404, detail="Lecturer not found.")
        return lecturer
    except IntegrityError as exc:
        handle_integrity_error(db, exc)


@app.delete("/api/lecturers/{lecturer_id}", status_code=204)
def delete_lecturer(lecturer_id: int, db: Session = Depends(get_db)):
    try:
        if not crud.delete_lecturer(db, lecturer_id):
            raise HTTPException(status_code=404, detail="Lecturer not found.")
    except IntegrityError as exc:
        handle_integrity_error(db, exc)


# -------------------------
# Courses
# -------------------------

@app.post(
    "/api/courses",
    response_model=schemas.CourseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_course(
    course: schemas.CourseCreate,
    db: Session = Depends(get_db),
):
    try:
        if crud.get_department(db, course.department_id) is None:
            raise HTTPException(status_code=422, detail="Department not found.")
        if crud.get_lecturer(db, course.lecturer_id) is None:
            raise HTTPException(status_code=422, detail="Lecturer not found.")
        return crud.create_course(db, course)
    except IntegrityError as exc:
        handle_integrity_error(db, exc)


@app.get("/api/courses", response_model=list[schemas.CourseResponse])
def read_courses(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return crud.get_courses(db, skip, limit)


@app.get("/api/courses/{course_id}", response_model=schemas.CourseResponse)
def read_course(course_id: int, db: Session = Depends(get_db)):
    course = crud.get_course(db, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found.")
    return course


@app.patch("/api/courses/{course_id}", response_model=schemas.CourseResponse)
def update_course(
    course_id: int,
    updates: schemas.CourseUpdate,
    db: Session = Depends(get_db),
):
    try:
        data = updates.model_dump(exclude_unset=True)
        validate_patch(data)
        if "department_id" in data and crud.get_department(db, data["department_id"]) is None:
            raise HTTPException(status_code=422, detail="Department not found.")
        if "lecturer_id" in data and crud.get_lecturer(db, data["lecturer_id"]) is None:
            raise HTTPException(status_code=422, detail="Lecturer not found.")
        course = crud.update_course(db, course_id, data)
        if course is None:
            raise HTTPException(status_code=404, detail="Course not found.")
        return course
    except IntegrityError as exc:
        handle_integrity_error(db, exc)


@app.delete("/api/courses/{course_id}", status_code=204)
def delete_course(course_id: int, db: Session = Depends(get_db)):
    try:
        if not crud.delete_course(db, course_id):
            raise HTTPException(status_code=404, detail="Course not found.")
    except IntegrityError as exc:
        handle_integrity_error(db, exc)


# -------------------------
# Exams
# -------------------------

@app.post(
    "/api/exams",
    response_model=schemas.ExamResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_exam(exam: schemas.ExamCreate, db: Session = Depends(get_db)):
    try:
        if crud.get_course(db, exam.course_id) is None:
            raise HTTPException(status_code=422, detail="Course not found.")
        return crud.create_exam(db, exam)
    except IntegrityError as exc:
        handle_integrity_error(db, exc)


@app.get("/api/exams", response_model=list[schemas.ExamResponse])
def read_exams(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return crud.get_exams(db, skip, limit)


@app.get("/api/exams/{exam_id}", response_model=schemas.ExamResponse)
def read_exam(exam_id: int, db: Session = Depends(get_db)):
    exam = crud.get_exam(db, exam_id)
    if exam is None:
        raise HTTPException(status_code=404, detail="Exam not found.")
    return exam


@app.patch("/api/exams/{exam_id}", response_model=schemas.ExamResponse)
def update_exam(
    exam_id: int,
    updates: schemas.ExamUpdate,
    db: Session = Depends(get_db),
):
    try:
        data = updates.model_dump(exclude_unset=True)
        validate_patch(data)
        if "course_id" in data and crud.get_course(db, data["course_id"]) is None:
            raise HTTPException(status_code=422, detail="Course not found.")
        exam = crud.update_exam(db, exam_id, data)
        if exam is None:
            raise HTTPException(status_code=404, detail="Exam not found.")
        return exam
    except IntegrityError as exc:
        handle_integrity_error(db, exc)


@app.delete("/api/exams/{exam_id}", status_code=204)
def delete_exam(exam_id: int, db: Session = Depends(get_db)):
    try:
        if not crud.delete_exam(db, exam_id):
            raise HTTPException(status_code=404, detail="Exam not found.")
    except IntegrityError as exc:
        handle_integrity_error(db, exc)
