import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, SessionDep
from app.model.pet import Pet, PetCreate, PetPublic, PetsPublic, PetUpdate
from app.models import Message
from app.model.insurance import Insurance, InsuranceUpdate
from app.model.vaccination import Vaccination, VaccinationCreate, VaccinationPublic
from app.model.allergi import Allergi, AllergiCreate, AllergiPublic

router = APIRouter(prefix="/pets", tags=["pets"])


@router.get("/", response_model=PetsPublic)
def read_pets(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve pets.
    """

    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Pet)
        count = session.exec(count_statement).one()
        statement = select(Pet).offset(skip).limit(limit)
        pets = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(Pet)
            .where(Pet.user_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Pet)
            .where(Pet.user_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        pets = session.exec(statement).all()

    return PetsPublic(data=pets, count=count)


@router.get("/{id}", response_model=PetPublic)
def read_pet(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get pet by ID.
    """
    pet = session.get(Pet, id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    if not current_user.is_superuser and (pet.user_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return pet


@router.post("/", response_model=PetPublic)
def create_pet(
    *, session: SessionDep, current_user: CurrentUser, pet_in: PetCreate
) -> Any:
    """
    Create new pet.
    """
    pet = Pet.model_validate(pet_in, update={"user_id": current_user.id})
    session.add(pet)
    session.commit()
    session.refresh(pet)
    return pet


@router.post("/{id}", response_model=PetPublic)
def update_pet(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    pet_in: PetUpdate,
) -> Any:
    """
    Update a pet.
    """
    pet = session.get(Pet, id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    if not current_user.is_superuser and (pet.user_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    update_dict = pet_in.model_dump(exclude_unset=True)
    pet.sqlmodel_update(update_dict)
    session.add(pet)
    session.commit()
    session.refresh(pet)
    return pet


@router.delete("/{id}")
def delete_pet(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a pet.
    """
    pet = session.get(Pet, id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    if not current_user.is_superuser and (pet.user_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(pet)
    session.commit()
    return Message(message="Pet deleted successfully")


class PetBioUpdate(BaseModel):
    bio: str | None = Field(default=None, max_length=65535)


@router.patch("/{id}/bio", response_model=PetPublic)
def update_pet_bio(
    *,
    session: SessionDep,
    id: uuid.UUID,
    bio_update: PetBioUpdate,
) -> Any:
    """
    Update a pet's bio.
    """
    pet = session.get(Pet, id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    
    pet.bio = bio_update.bio
    session.add(pet)
    session.commit()
    session.refresh(pet)
    return pet


class PetProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    type: str | None = Field(default=None, max_length=100)
    breed: str | None = Field(default=None, max_length=255)
    gender: str | None = Field(default=None, max_length=20)
    age: int | None = Field(default=None)
    weight: float | None = Field(default=None)


@router.patch("/{id}/profile", response_model=PetPublic)
def update_pet_profile(
    *,
    session: SessionDep,
    id: uuid.UUID,
    profile_update: PetProfileUpdate,
) -> Any:
    """
    Update a pet's profile information.
    """
    pet = session.get(Pet, id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    
    update_dict = profile_update.model_dump(exclude_unset=True)
    pet.sqlmodel_update(update_dict)
    session.add(pet)
    session.commit()
    session.refresh(pet)
    return pet


class PetFavoritesUpdate(BaseModel):
    favorite_food: str | None = Field(default=None, max_length=255)
    favorite_toy: str | None = Field(default=None, max_length=255)
    favorite_activity: str | None = Field(default=None, max_length=500)


@router.patch("/{id}/favorites", response_model=PetPublic)
def update_pet_favorites(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    favorites_update: PetFavoritesUpdate,
) -> Any:
    """
    Update a pet's favorite things.
    """
    pet = session.get(Pet, id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    if not current_user.is_superuser and (pet.user_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    update_dict = favorites_update.model_dump(exclude_unset=True)
    pet.sqlmodel_update(update_dict)
    session.add(pet)
    session.commit()
    session.refresh(pet)
    return pet


class PetBehaviorUpdate(BaseModel):
    aggresive: bool | None = Field(default=None)
    pulls: bool | None = Field(default=None)
    strangers: bool | None = Field(default=None)


@router.patch("/{id}/behavior", response_model=PetPublic)
def update_pet_behavior(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    behavior_update: PetBehaviorUpdate,
) -> Any:
    """
    Update a pet's behavior information.
    """
    pet = session.get(Pet, id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    if not current_user.is_superuser and (pet.user_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    update_dict = behavior_update.model_dump(exclude_unset=True)
    pet.sqlmodel_update(update_dict)
    session.add(pet)
    session.commit()
    session.refresh(pet)
    return pet


class PetRoutineUpdate(BaseModel):
    walk_time: str | None = Field(default=None, max_length=500)
    feeding_time: str | None = Field(default=None, max_length=500)
    evening_routine: str | None = Field(default=None, max_length=500)


@router.patch("/{id}/routine", response_model=PetPublic)
def update_pet_routine(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    routine_update: PetRoutineUpdate,
) -> Any:
    """
    Update a pet's daily routine.
    """
    pet = session.get(Pet, id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    if not current_user.is_superuser and (pet.user_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    update_dict = routine_update.model_dump(exclude_unset=True)
    pet.sqlmodel_update(update_dict)
    session.add(pet)
    session.commit()
    session.refresh(pet)
    return pet


class PetInsuranceUpdate(BaseModel):
    provider: str | None = Field(default=None, max_length=255)
    policy: str | None = Field(default=None, max_length=255)
    coverage: str | None = Field(default=None, max_length=500)
    deductible: str | None = Field(default=None, max_length=100)
    reimbursement: str | None = Field(default=None, max_length=100)
    expires: str | None = Field(default=None, max_length=100)
    emergency_hotline: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=65535)


@router.patch("/{id}/insurance", response_model=PetPublic)
def update_pet_insurance(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    insurance_update: PetInsuranceUpdate,
) -> Any:
    
    """
    Update a pet's insurance information.
    """
    pet = session.get(Pet, id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    if not current_user.is_superuser and (pet.user_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    # Get or create insurance record for this pet
    insurance = session.exec(
        select(Insurance).where(Insurance.pet_id == id)
    ).first()
    
    if not insurance:
        # Create new insurance record
        insurance_data = insurance_update.model_dump(exclude_unset=True)
        insurance = Insurance(**insurance_data, pet_id=id)
        session.add(insurance)
    else:
        # Update existing insurance record
        update_dict = insurance_update.model_dump(exclude_unset=True)
        insurance.sqlmodel_update(update_dict)
        session.add(insurance)
    
    session.commit()
    session.refresh(pet)
    return pet


# Vaccination APIs
@router.post("/{id}/vaccinations", response_model=VaccinationPublic)
def add_pet_vaccination(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    vaccination_in: VaccinationCreate,
) -> Any:
    """
    Add a vaccination record to a pet.
    """
    pet = session.get(Pet, id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    if not current_user.is_superuser and (pet.user_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    vaccination = Vaccination.model_validate(vaccination_in, update={"pet_id": id})
    session.add(vaccination)
    session.commit()
    session.refresh(vaccination)
    return vaccination


@router.delete("/{id}/vaccinations/{vaccination_id}")
def remove_pet_vaccination(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    vaccination_id: uuid.UUID,
) -> Message:
    """
    Remove a vaccination record from a pet.
    """
    pet = session.get(Pet, id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    if not current_user.is_superuser and (pet.user_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    vaccination = session.get(Vaccination, vaccination_id)
    if not vaccination or vaccination.pet_id != id:
        raise HTTPException(status_code=404, detail="Vaccination not found")
    
    session.delete(vaccination)
    session.commit()
    return Message(message="Vaccination deleted successfully")


# Allergy APIs
@router.post("/{id}/allergies", response_model=AllergiPublic)
def add_pet_allergy(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    allergy_in: AllergiCreate,
) -> Any:
    """
    Add an allergy record to a pet.
    """
    pet = session.get(Pet, id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    if not current_user.is_superuser and (pet.user_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    allergy = Allergi.model_validate(allergy_in, update={"pet_id": id})
    session.add(allergy)
    session.commit()
    session.refresh(allergy)
    return allergy


@router.delete("/{id}/allergies/{allergy_id}")
def remove_pet_allergy(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    allergy_id: uuid.UUID,
) -> Message:
    """
    Remove an allergy record from a pet.
    """
    pet = session.get(Pet, id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    if not current_user.is_superuser and (pet.user_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    allergy = session.get(Allergi, allergy_id)
    if not allergy or allergy.pet_id != id:
        raise HTTPException(status_code=404, detail="Allergy not found")
    
    session.delete(allergy)
    session.commit()
    return Message(message="Allergy deleted successfully")
