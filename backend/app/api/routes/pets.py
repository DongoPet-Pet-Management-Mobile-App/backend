import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.model.pet import Pet, PetCreate, PetPublic, PetsPublic, PetUpdate
from app.models import Message

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


@router.put("/{id}", response_model=PetPublic)
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

