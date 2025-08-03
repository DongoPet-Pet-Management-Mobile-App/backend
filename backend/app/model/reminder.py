import uuid
from datetime import datetime, date, time
from typing import Optional
from sqlmodel import Field, Relationship, SQLModel

from app.model.user import User
from app.model.pet import Pet


class ReminderBase(SQLModel):
    category: str = Field(max_length=50)  # 'Food', 'Walk', 'Medication', 'Grooming', 'Vet appointment', 'Other'
    title: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None)
    date: date | None = Field(default=None)  # Single date for most reminders
    start_date: date | None = Field(default=None)  # For medication duration
    end_date: date | None = Field(default=None)  # For medication duration
    time: time = Field()
    dosage: str | None = Field(default=None, max_length=100)  # Only for medication
    frequency: str = Field(max_length=100)  # 'Never', 'Hourly', 'Daily', 'Weekly', 'Monthly', or custom
    end_frequency_date: date | None = Field(default=None)  # When to stop recurring
    is_active: bool = Field(default=True)


class Reminder(ReminderBase, table=True):
    __tablename__ = "reminders"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    pet_id: uuid.UUID = Field(foreign_key="pet.id", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: User | None = Relationship(back_populates="reminders")
    pet: Pet | None = Relationship(back_populates="reminders")


class ReminderCreate(ReminderBase):
    pass


class ReminderUpdate(SQLModel):
    category: str | None = None
    title: str | None = None
    notes: str | None = None
    date: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    time: time | None = None
    dosage: str | None = None
    frequency: str | None = None
    end_frequency_date: date | None = None
    is_active: bool | None = None


class ReminderPublic(ReminderBase):
    id: uuid.UUID
    user_id: uuid.UUID
    pet_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class RemindersPublic(SQLModel):
    data: list[ReminderPublic]
    count: int