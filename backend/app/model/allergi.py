import uuid
from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel
from app.model.pet import Pet


class AllergiBase(SQLModel):
    name: str | None = Field(default=None, max_length=255)


class AllergiCreate(AllergiBase):
    pass


class AllergiUpdate(AllergiBase):
    pass


class Allergi(AllergiBase, table=True):
    __tablename__ = "allergi"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    pet_id: uuid.UUID = Field(
        foreign_key="pet.id", nullable=False, ondelete="CASCADE"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    pet: Pet | None = Relationship(back_populates="allergis")


class AllergiPublic(AllergiBase):
    id: uuid.UUID
    pet_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class AllergisPublic(SQLModel):
    data: list[AllergiPublic]
    count: int