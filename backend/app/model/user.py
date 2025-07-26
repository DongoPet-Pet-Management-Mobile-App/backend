import uuid
from datetime import datetime
from email.policy import default

from pydantic import EmailStr
from sqlmodel import Field, SQLModel, Relationship
from typing_extensions import Optional, List


class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    name: str = Field(max_length=255)
    full_name: str | None = Field(default=None, max_length=255)
    email: str = Field(unique=True, index=True, max_length=255)
    phone_number: str | None = Field(default=None, max_length=20)
    address: str | None = Field(default=None, max_length=500)
    password: str = Field(min_length=8, max_length=128)
    hashed_password: str = Field(default=None, nullable=True)
    language: str | None = Field(default=None, max_length=64)
    notification: bool = Field(default=True)
    membership: int | None = Field(default=0)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    pets: list["Pet"] = Relationship(back_populates="owner")

# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    name: Optional[str] = Field(default=None, max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=255)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = Field(default=None, max_length=500)
    language: Optional[str] = Field(default=None, max_length=64)
    notification: Optional[bool] = Field(default=True)
    membership: Optional[int] = Field(default=0)
    is_active: Optional[bool] = Field(default=True)
    is_superuser: Optional[bool] = Field(default=False)

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)

# Properties to receive via API on registration (signup)
class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    name: Optional[str] = Field(default=None, max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=255)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = Field(default=None, max_length=500)
    language: Optional[str] = Field(default=None, max_length=64)
    notification: Optional[bool] = Field(default=True)

# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: Optional[EmailStr] = Field(default=None, max_length=255)
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)

class UserUpdateMe(SQLModel):
    name: Optional[str] = Field(default=None, max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=255)
    email: Optional[EmailStr] = Field(default=None, max_length=255)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = Field(default=None, max_length=500)
    language: Optional[str] = Field(default=None, max_length=64)
    notification: Optional[bool] = Field(default=None)

# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID

class UsersPublic(SQLModel):
    data: List[UserPublic]
    count: int

class UpdatePassword(SQLModel):
    current_password: str
    new_password: str

class SelectTeacherRequest(SQLModel):
    teacher: str  # or UUID if you use UUIDs for teacher IDs

class SelectLanguageRequest(SQLModel):
    language: str  # or UUID if you use UUIDs for teacher IDs
