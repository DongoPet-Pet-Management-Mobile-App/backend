import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.model.food_scan_result import FoodScanResult, FoodScanResultsPublic

router = APIRouter(prefix="/food-scan-results", tags=["food-scan-results"])


@router.get("/{pet_id}", response_model=FoodScanResultsPublic)
def get_pet_food_scan_results(
    session: SessionDep, 
    current_user: CurrentUser, 
    pet_id: uuid.UUID
) -> Any:
    """
    Get all food scan results for a specific pet.
    """
    # Verify pet ownership
    from app.model.pet import Pet
    pet = session.get(Pet, pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    if pet.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    # Get food scan results
    statement = select(FoodScanResult).where(FoodScanResult.pet_id == pet_id)
    results = session.exec(statement).all()
    
    return FoodScanResultsPublic(data=results, count=len(results))