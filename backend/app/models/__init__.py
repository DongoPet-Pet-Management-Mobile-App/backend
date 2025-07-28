from pydantic import BaseModel
from sqlmodel import SQLModel, Field

from app.model.user import User
from app.model.pet import Pet
from app.model.insurance import Insurance
from app.model.medical_condition import MedicalCondition
from app.model.medication import Medication
from app.model.vaccination import Vaccination
from app.model.allergi import Allergi
from app.model.food_scan_result import FoodScanResult

__all__ = ["User", "Pet", "Insurance", "MedicalCondition", "Medication", "Vaccination", "Allergi", "FoodScanResult"]

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    message: str

# Generic message
class Message(SQLModel):
    message: str

# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None

# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)



