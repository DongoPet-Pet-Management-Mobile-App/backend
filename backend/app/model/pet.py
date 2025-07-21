import uuid
from sqlmodel import Field, Relationship, SQLModel
from app.model.user import User

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


# Properties to return via API, id is always required
class PetPublic(PetBase):
    id: uuid.UUID
    user_id: uuid.UUID


class PetsPublic(SQLModel):
    data: list[PetPublic]
    count: int
