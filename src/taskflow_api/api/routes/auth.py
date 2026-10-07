from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from taskflow_api.api.schemas.auth import TokenResponse
from taskflow_api.core.security import create_access_token, verify_password
from taskflow_api.db.models.user import User
from taskflow_api.dependencies.database import get_db

router = APIRouter()


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
):
    existing_user: User | None = db.scalar(
        select(User).where(User.email == form_data.username)
    )
    if not existing_user or not verify_password(
        form_data.password, existing_user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    access_token = create_access_token(existing_user.id)
    return {"access_token": access_token, "token_type": "bearer"}
