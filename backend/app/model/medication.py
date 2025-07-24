import uuid
from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel
from app.model.pet import Pet


class MedicationBase(SQLModel):
    name: str | None = Field(default=None, max_length=255)
    dosage: str | None = Field(default=None, max_length=255)
    frequency: str | None = Field(default=None, max_length=255)
    start_end: str | None = Field(default=None, max_length=255)
    note: str | None = Field(default=None, max_length=65535)


class MedicationCreate(MedicationBase):
    pass


class MedicationUpdate(MedicationBase):
    pass


class Medication(MedicationBase, table=True):
    __tablename__ = "medication"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    pet_id: uuid.UUID = Field(
        foreign_key="pet.id", nullable=False, ondelete="CASCADE"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    pet: Pet | None = Relationship(back_populates="medications")


class MedicationPublic(MedicationBase):
    id: uuid.UUID
    pet_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class MedicationsPublic(SQLModel):
    data: list[MedicationPublic]
    count: int