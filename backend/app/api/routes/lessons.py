import uuid

from fastapi import APIRouter, HTTPException, status
from typing_extensions import Any
from app.api.deps import SessionDep
from app.model.lesson import LessonCreate, Lesson, LessonsPublic, LessonUpdate

router = APIRouter(prefix="/lessons", tags=["lessons"])

@router.get("/", response_model=LessonsPublic)
def get_lessons(
    session: SessionDep, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve all lessons
    """
    from sqlmodel import select, func
    from app.model.lesson import Lesson

    count_statement = select(func.count()).select_from(Lesson)
    count = session.exec(count_statement).one()

    statement = select(Lesson).offset(skip).limit(limit)
    lessons = session.exec(statement).all()

    return LessonsPublic(data=lessons, count=count)

@router.post("/", response_model=Lesson, status_code=status.HTTP_201_CREATED)
def create_lesson_endpoint(
    *, session: SessionDep, item_in: LessonCreate, owner_id: uuid.UUID
) -> Any:
    """
    Create new lesson
    """
    db_lesson = Lesson.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_lesson)
    session.commit()
    session.refresh(db_lesson)
    return db_lesson

@router.post("/{lesson_id}", response_model=Lesson)
def update_lesson(
    *, session: SessionDep, lesson_id: uuid.UUID, item_in: LessonUpdate
) -> Any:
    """
    Update an existing lesson
    """
    lesson = session.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    lesson_data = item_in.model_dump(exclude_unset=True)
    for key, value in lesson_data.items():
        setattr(lesson, key, value)
    session.add(lesson)
    session.commit()
    session.refresh(lesson)
    return lesson

@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(
    *, session: SessionDep, lesson_id: uuid.UUID
) -> None:
    """
    Delete a lesson
    """
    lesson = session.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    session.delete(lesson)
    session.commit()
    return None
