from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from taskflow_api.api.schemas.users import UserCreate, UserResponse
from taskflow_api.core.security import hash_password
from taskflow_api.db.database import get_db
from taskflow_api.db.models.user import User
from taskflow_api.dependencies.auth import get_current_user

router = APIRouter()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(data: UserCreate, db: Annotated[Session, Depends(get_db)]):
    existing_user = db.scalar(select(User).where(User.email == data.email))

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already created with this email",
        )

    new_user = User(email=data.email, password_hash=hash_password(data.password))

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get("/me", response_model=UserResponse)
def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
