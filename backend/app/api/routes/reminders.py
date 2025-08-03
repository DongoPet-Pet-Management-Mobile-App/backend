import uuid
from typing import Any
from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.model.reminder import Reminder, ReminderCreate, ReminderPublic, RemindersPublic, ReminderUpdate
from app.models import Message

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("/", response_model=RemindersPublic)
def read_reminders(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve reminders for current user.
    """
    count_statement = select(func.count()).select_from(Reminder).where(Reminder.user_id == current_user.id)
    count = session.exec(count_statement).one()
    
    statement = select(Reminder).where(Reminder.user_id == current_user.id).offset(skip).limit(limit)
    reminders = session.exec(statement).all()
    
    return RemindersPublic(data=reminders, count=count)


@router.get("/{id}", response_model=ReminderPublic)
def read_reminder(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get reminder by ID.
    """
    reminder = session.get(Reminder, id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    if reminder.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return reminder


@router.post("/", response_model=ReminderPublic)
def create_reminder(
    *, session: SessionDep, current_user: CurrentUser, reminder_in: ReminderCreate
) -> Any:
    """
    Create new reminder.
    """
    reminder = Reminder.model_validate(reminder_in, update={"user_id": current_user.id})
    session.add(reminder)
    session.commit()
    session.refresh(reminder)
    return reminder


@router.patch("/{id}", response_model=ReminderPublic)
def update_reminder(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    reminder_in: ReminderUpdate,
) -> Any:
    """
    Update a reminder.
    """
    reminder = session.get(Reminder, id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    if reminder.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    update_dict = reminder_in.model_dump(exclude_unset=True)
    reminder.sqlmodel_update(update_dict)
    session.add(reminder)
    session.commit()
    session.refresh(reminder)
    return reminder


@router.delete("/{id}")
def delete_reminder(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a reminder.
    """
    reminder = session.get(Reminder, id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    if reminder.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    session.delete(reminder)
    session.commit()
    return Message(message="Reminder deleted successfully")


@router.get("/pet/{pet_id}", response_model=RemindersPublic)
def read_pet_reminders(
    session: SessionDep, current_user: CurrentUser, pet_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> Any:
    """
    Get all reminders for a specific pet.
    """
    count_statement = select(func.count()).select_from(Reminder).where(
        Reminder.user_id == current_user.id, Reminder.pet_id == pet_id
    )
    count = session.exec(count_statement).one()
    
    statement = select(Reminder).where(
        Reminder.user_id == current_user.id, Reminder.pet_id == pet_id
    ).offset(skip).limit(limit)
    reminders = session.exec(statement).all()
    
    return RemindersPublic(data=reminders, count=count)