from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class DepartmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class LecturerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=255)
    department_id: int = Field(gt=0)


class LecturerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(default=None, min_length=3, max_length=255)
    department_id: int | None = Field(default=None, gt=0)


class LecturerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    department_id: int


class CourseCreate(BaseModel):
    course_code: str = Field(min_length=1, max_length=20)
    title: str = Field(min_length=1, max_length=200)
    ects: int = Field(gt=0, le=60)
    department_id: int = Field(gt=0)
    lecturer_id: int = Field(gt=0)


class CourseUpdate(BaseModel):
    course_code: str | None = Field(default=None, min_length=1, max_length=20)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    ects: int | None = Field(default=None, gt=0, le=60)
    department_id: int | None = Field(default=None, gt=0)
    lecturer_id: int | None = Field(default=None, gt=0)


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_code: str
    title: str
    ects: int
    department_id: int
    lecturer_id: int


class ExamCreate(BaseModel):
    exam_date: datetime
    room: str = Field(min_length=1, max_length=50)
    course_id: int = Field(gt=0)


class ExamUpdate(BaseModel):
    exam_date: datetime | None = None
    room: str | None = Field(default=None, min_length=1, max_length=50)
    course_id: int | None = Field(default=None, gt=0)


class ExamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exam_date: datetime
    room: str
    course_id: int
