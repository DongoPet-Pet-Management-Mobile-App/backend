import uuid

from sqlmodel import Field, SQLModel
from typing_extensions import Optional, List

from app.constants import LessonStatus
from app.model.lesson import Lesson


# Shared properties
class ProgressLessonBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ProgressLessonCreate(ProgressLessonBase):
    pass


# Properties to receive on item update
class ProgressLessonUpdate(ProgressLessonBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class ProgressLesson(ProgressLessonBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    teacher_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    lesson_id: uuid.UUID = Field(foreign_key="lesson.id", nullable=False)
    progress: int | None = Field(default=0, description="Current Progress of lesson")
    status: int | None = Field(default=LessonStatus.disable, description="Current status of user's lesson")

# Properties to return via API, id is always required
class ProgressLessonPublic(ProgressLessonBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ProgressLessonsPublic(SQLModel):
    data: list[ProgressLessonPublic]
    count: int

class ProgressLessonWithLesson(SQLModel):
    progress: ProgressLesson
    lesson: Lesson

class LessonWithProgress(SQLModel):
    lesson: Lesson
    progress: Optional[ProgressLesson]  # Will be None if no progress

class LessonsWithProgressResponse(SQLModel):
    data: List[LessonWithProgress]
    count: int