import uuid
from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel
from app.model.pet import Pet


class InsuranceBase(SQLModel):
    provider: str | None = Field(default=None, max_length=255)
    policy: str | None = Field(default=None, max_length=255)
    coverage: str | None = Field(default=None, max_length=500)
    deductible: str | None = Field(default=None, max_length=100)
    reimbursement: str | None = Field(default=None, max_length=100)
    expires: str | None = Field(default=None, max_length=100)
    emergency_hotline: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=65535)


# Properties to receive on insurance creation
class InsuranceCreate(InsuranceBase):
    pass


# Properties to receive on insurance update
class InsuranceUpdate(InsuranceBase):
    pass


# Database model, database table inferred from class name
class Insurance(InsuranceBase, table=True):
    __tablename__ = "insurance"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    pet_id: uuid.UUID = Field(
        foreign_key="pet.id", nullable=False, ondelete="CASCADE"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    pet: Pet | None = Relationship(back_populates="insurance")


# Properties to return via API, id is always required
class InsurancePublic(InsuranceBase):
    id: uuid.UUID
    pet_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class InsurancesPublic(SQLModel):
    data: list[InsurancePublic]
    count: int