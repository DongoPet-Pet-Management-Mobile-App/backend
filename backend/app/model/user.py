import uuid
from datetime import datetime
from email.policy import default

from pydantic import EmailStr
from sqlmodel import Field, SQLModel, Relationship
from typing_extensions import Optional, List


class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    name: str = Field(max_length=255)
    email: str = Field(unique=True, index=True, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    native_language: str | None = Field(default=None, max_length=64)
    purpose_language: str | None = Field(default=None, max_length=256)
    reason: str | None = Field(default=None, max_length=255)
    time: int | None = Field(default=None, description="Learning time in minutes")
    teacher: str | None = Field(default=None, max_length=255)  # teacher id
    current_lesson: str | None = Field(default=None, max_length=255) # lesson id
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    extra_minute: int | None = Field(default=0)
    membership: int | None = Field(default=0)
    hashed_password: str = Field(default=None, nullable=True)
    items: list["Item"] = Relationship(back_populates="owner")

# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    name: Optional[str] = Field(default=None, max_length=255)
    native_language: Optional[str] = Field(default=None, max_length=64)
    purpose_language: Optional[str] = Field(default=None, max_length=256)
    reason: Optional[str] = Field(default=None, max_length=255)
    time: Optional[int] = Field(default=None, description="Learning time in minutes")
    teacher: Optional[str] = Field(default=None, max_length=255)
    current_lesson: Optional[str] = Field(default=None, max_length=255)
    extra_minute: Optional[int] = Field(default=0)
    membership: Optional[int] = Field(default=0)

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)

# Properties to receive via API on registration (signup)
class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    name: Optional[str] = Field(default=None, max_length=255)
    native_language: Optional[str] = Field(default=None, max_length=64)
    purpose_language: Optional[str] = Field(default=None, max_length=64)
    reason: Optional[str] = Field(default=None, max_length=255)
    time: int | None = Field(default=None, description="Learning time in minutes")

# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: Optional[EmailStr] = Field(default=None, max_length=255)
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)

class UserUpdateMe(SQLModel):
    name: Optional[str] = Field(default=None, max_length=255)
    email: Optional[EmailStr] = Field(default=None, max_length=255)
    native_language: Optional[str] = Field(default=None, max_length=64)
    purpose_language: Optional[str] = Field(default=None, max_length=64)
    reason: Optional[str] = Field(default=None, max_length=255)

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
