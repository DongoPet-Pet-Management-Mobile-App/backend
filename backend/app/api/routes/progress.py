import uuid

from fastapi import APIRouter, HTTPException, Depends
from typing_extensions import Any

from app.api.deps import SessionDep, get_current_user
from app.constants import LessonStatus
from app.model.lesson import Lesson
from app.model.user import User

router = APIRouter(prefix="/progress", tags=["progress"])

from app.model.progress_lesson import (
    ProgressLesson,
    ProgressLessonCreate,
    ProgressLessonUpdate,
    ProgressLessonsPublic, ProgressLessonWithLesson, LessonsWithProgressResponse, LessonWithProgress,
)

from sqlmodel import Session, select

def create_progress_lesson(
    session: Session, item_in: ProgressLessonCreate, owner_id: uuid.UUID
) -> ProgressLesson:
    db_obj = ProgressLesson.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj

def get_progress_lessons_by_user(
    session: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100
):
    statement = select(ProgressLesson).where(ProgressLesson.user_id == user_id).offset(skip).limit(limit)
    return session.exec(statement).all()

def update_progress_lesson(
    session: Session, lesson_id: uuid.UUID, item_in: ProgressLessonUpdate
) -> ProgressLesson:
    db_obj = session.get(ProgressLesson, lesson_id)
    if not db_obj:
        return None
    obj_data = item_in.model_dump(exclude_unset=True)
    for key, value in obj_data.items():
        setattr(db_obj, key, value)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj

@router.post("/", response_model=ProgressLesson)
def create_progress_lesson_endpoint(
    *, session: SessionDep, item_in: ProgressLessonCreate, owner_id: uuid.UUID
):
    return create_progress_lesson(session, item_in, owner_id)

@router.get("/user/{user_id}", response_model=ProgressLessonsPublic)
def get_user_progress_lessons(
    *, session: SessionDep, user_id: uuid.UUID, skip: int = 0, limit: int = 100
):
    lessons = get_progress_lessons_by_user(session, user_id, skip, limit)
    return ProgressLessonsPublic(data=lessons, count=len(lessons))

@router.post("/{progress_lesson_id}", response_model=ProgressLesson)
def update_progress_lesson_endpoint(
    *, session: SessionDep, progress_lesson_id: uuid.UUID, item_in: ProgressLessonUpdate
):
    updated = update_progress_lesson(session, progress_lesson_id, item_in)
    if not updated:
        raise HTTPException(status_code=404, detail="ProgressLesson not found")
    return updated

@router.get("/user/{user_id}/current", response_model=ProgressLessonWithLesson)
def get_current_progressing_lesson(
    *, session: SessionDep, user_id: uuid.UUID
):
    # Find the current progressing lesson for the user
    progress = session.exec(
        select(ProgressLesson)
        .where(
            ProgressLesson.user_id == user_id,
            ProgressLesson.status == LessonStatus.in_progress  # or whatever status means "current"
        )
        .order_by(ProgressLesson.id.desc())
    ).first()

    if not progress:
        raise HTTPException(status_code=404, detail="No current progressing lesson found")

    lesson = session.get(Lesson, progress.lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    return ProgressLessonWithLesson(progress=progress, lesson=lesson)

@router.get("/with-progress/", response_model=LessonsWithProgressResponse)
def get_lessons_with_progress(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get all lessons with progress for the current user (from token).
    If no progress exists for a lesson, return default progress (status=disable).
    """
    from sqlmodel import select

    # Get all lessons
    lessons = session.exec(select(Lesson).offset(skip).limit(limit)).all()
    lesson_ids = [lesson.id for lesson in lessons]

    # Get all progress for this user and these lessons
    progresses = session.exec(
        select(ProgressLesson).where(
            ProgressLesson.user_id == current_user.id,
            ProgressLesson.lesson_id.in_(lesson_ids)
        )
    ).all()
    progress_map = {p.lesson_id: p for p in progresses}

    # Build response
    result = []
    for lesson in lessons:
        progress = progress_map.get(lesson.id)
        if not progress:
            # Create a default progress object (not persisted in DB)
            progress = ProgressLesson(
                id=uuid.uuid4(),
                owner_id=current_user.id,
                teacher_id=None,
                user_id=current_user.id,
                lesson_id=lesson.id,
                progress=0,
                status=LessonStatus.disable,
                title=lesson.title,
                description=lesson.description,
            )
        result.append(LessonWithProgress(lesson=lesson, progress=progress))

    return LessonsWithProgressResponse(data=result, count=len(result))