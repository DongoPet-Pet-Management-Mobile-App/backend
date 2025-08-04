import uuid
from datetime import datetime, date, time
from typing import Optional
from sqlmodel import Field, Relationship, SQLModel

from app.model.pet import Pet


class ReminderBase(SQLModel):
    category: str = Field(max_length=50)  # 'Food', 'Walk', 'Medication', 'Grooming', 'Vet appointment', 'Other'
    title: Optional[str] = Field(default=None, max_length=255)
    notes: Optional[str] = Field(default=None)
    reminder_date: Optional[date] = Field(default=None)  # Single date for most reminders
    start_date: Optional[date] = Field(default=None)  # For medication duration
    end_date: Optional[date] = Field(default=None)  # For medication duration
    reminder_time: time = Field()
    dosage: Optional[str] = Field(default=None, max_length=100)  # Only for medication
    frequency: str = Field(max_length=100)  # 'Never', 'Hourly', 'Daily', 'Weekly', 'Monthly', or custom
    end_frequency_date: Optional[date] = Field(default=None)  # When to stop recurring
    is_active: bool = Field(default=True)


class Reminder(ReminderBase, table=True):
    __tablename__ = "reminders"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    pet_id: uuid.UUID = Field(foreign_key="pet.id", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    pet: Optional[Pet] = Relationship(back_populates="reminders")


class ReminderCreate(ReminderBase):
    pass


class ReminderUpdate(SQLModel):
    category: Optional[str] = None
    title: Optional[str] = None
    notes: Optional[str] = None
    reminder_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    reminder_time: Optional[time] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    end_frequency_date: Optional[date] = None
    is_active: Optional[bool] = None


class ReminderPublic(ReminderBase):
    id: uuid.UUID
    pet_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class RemindersPublic(SQLModel):
    data: list[ReminderPublic]
    count: int


