import uuid
from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel
from app.model.pet import Pet


class MedicalConditionBase(SQLModel):
    name: str | None = Field(default=None, max_length=255)
    note: str | None = Field(default=None, max_length=65535)


class MedicalConditionCreate(MedicalConditionBase):
    pass


class MedicalConditionUpdate(MedicalConditionBase):
    pass


class MedicalCondition(MedicalConditionBase, table=True):
    __tablename__ = "medical_condition"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    pet_id: uuid.UUID = Field(
        foreign_key="pet.id", nullable=False, ondelete="CASCADE"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    pet: Pet | None = Relationship(back_populates="medical_conditions")


class MedicalConditionPublic(MedicalConditionBase):
    id: uuid.UUID
    pet_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class MedicalConditionsPublic(SQLModel):
    data: list[MedicalConditionPublic]
    count: int