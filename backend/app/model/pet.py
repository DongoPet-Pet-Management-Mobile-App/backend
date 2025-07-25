import uuid
from sqlmodel import Field, Relationship, SQLModel
from app.model.user import User
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.model.insurance import Insurance
    from app.model.medical_condition import MedicalCondition
    from app.model.medication import Medication
    from app.model.vaccination import Vaccination
    from app.model.allergi import Allergi

class PetBase(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    type: str | None = Field(default=None, max_length=100)
    gender: str | None = Field(default=None, max_length=20)
    age: int | None = Field(default=None)
    breed: str | None = Field(default=None, max_length=255)
    weight: float | None = Field(default=None)
    allergi: str | None = Field(default=None, max_length=500)
    vaccination: str | None = Field(default=None, max_length=500)
    color: str | None = Field(default=None, max_length=100)
    height: float | None = Field(default=None)
    relationship: str | None = Field(default=None, max_length=100)
    avatar: str | None = Field(default=None, max_length=500)
    chipnumber: str | None = Field(default=None, max_length=50)
    bio: str | None = Field(default=None, max_length=65535)
    favorite_food: str | None = Field(default=None, max_length=255)
    favorite_toy: str | None = Field(default=None, max_length=255)
    favorite_activity: str | None = Field(default=None, max_length=500)
    aggresive : bool | None = Field(default=False)
    pulls : bool | None = Field(default=False)
    strangers: bool | None = Field(default=False)
    walk_time: str | None = Field(default=None, max_length=500)   
    feeding_time: str | None = Field(default=None, max_length=500)   
    evening_routine: str | None = Field(default=None, max_length=500)   


# Properties to receive on pet creation
class PetCreate(PetBase):
    pass


# Properties to receive on pet update
class PetUpdate(PetBase):
    name: str | None = Field(default=None, min_length=1, max_length=255)


# Database model, database table inferred from class name
class Pet(PetBase, table=True):
    __tablename__ = "pet"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="pets")
    insurance: list["Insurance"] = Relationship(back_populates="pet")
    medical_conditions: list["MedicalCondition"] = Relationship(back_populates="pet")
    medications: list["Medication"] = Relationship(back_populates="pet")
    vaccinations: list["Vaccination"] = Relationship(back_populates="pet")
    allergies: list["Allergi"] = Relationship(back_populates="pet")


# Properties to return via API, id is always required
class PetPublic(PetBase):
    id: uuid.UUID
    user_id: uuid.UUID


class PetsPublic(SQLModel):
    data: list[PetPublic]
    count: int
