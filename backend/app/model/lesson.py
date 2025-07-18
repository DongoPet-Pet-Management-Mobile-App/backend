import uuid
from email.policy import default

from sqlmodel import Field, SQLModel, Relationship


# Shared properties
class LessonBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class LessonCreate(LessonBase):
    pass


# Properties to receive on item update
class LessonUpdate(LessonBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Lesson(LessonBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    type: int | None = Field(default=None)
    unit: int | None = Field(default=1)
    subunit: int | None = Field(default=1)
    detail: str | None = Field(default=None, max_length=65536)


# Properties to return via API, id is always required
class LessonPublic(LessonBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class LessonsPublic(SQLModel):
    data: list[LessonPublic]
    count: int