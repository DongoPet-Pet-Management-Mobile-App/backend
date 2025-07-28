import uuid
from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel
from app.model.pet import Pet


class FoodScanResultBase(SQLModel):
    # Food item details (flattened from foodItems[0])
    food_name: str | None = Field(default=None, max_length=255)
    calories: int | None = Field(default=None)
    protein: float | None = Field(default=None)
    carbs: float | None = Field(default=None)
    fat: float | None = Field(default=None)
    fiber: float | None = Field(default=None)
    moisture: float | None = Field(default=None)
    
    # Pet safety info (flattened from petSafety)
    is_safe: bool | None = Field(default=None)
    safety_message: str | None = Field(default=None, max_length=500)
    toxic_ingredients: str | None = Field(default=None, max_length=1000)  # JSON string of array
    
    # Health score info
    nutrition_health_score: int | None = Field(default=None)
    health_score_description: str | None = Field(default=None, max_length=1000)
    health_score_recommendations: str | None = Field(default=None, max_length=1000)
    
    # Additional fields
    has_multiple_items: bool | None = Field(default=False)


class FoodScanResultCreate(FoodScanResultBase):
    pass


class FoodScanResultUpdate(FoodScanResultBase):
    pass


class FoodScanResult(FoodScanResultBase, table=True):
    __tablename__ = "food_scan_result"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    pet_id: uuid.UUID = Field(
        foreign_key="pet.id", nullable=False, ondelete="CASCADE"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    pet: Pet | None = Relationship(back_populates="food_scan_results")


class FoodScanResultPublic(FoodScanResultBase):
    id: uuid.UUID
    pet_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class FoodScanResultsPublic(SQLModel):
    data: list[FoodScanResultPublic]
    count: int