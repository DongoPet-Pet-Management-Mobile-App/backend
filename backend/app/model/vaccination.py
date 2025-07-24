import uuid
from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel
from app.model.pet import Pet


class VaccinationBase(SQLModel):
    name: str | None = Field(default=None, max_length=255)
    date: str | None = Field(default=None, max_length=100)


class VaccinationCreate(VaccinationBase):
    pass


class VaccinationUpdate(VaccinationBase):
    pass


class Vaccination(VaccinationBase, table=True):
    __tablename__ = "vaccination"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    pet_id: uuid.UUID = Field(
        foreign_key="pet.id", nullable=False, ondelete="CASCADE"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    pet: Pet | None = Relationship(back_populates="vaccinations")


class VaccinationPublic(VaccinationBase):
    id: uuid.UUID
    pet_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class VaccinationsPublic(SQLModel):
    data: list[VaccinationPublic]
    count: int