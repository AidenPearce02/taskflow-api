from typing import Annotated, NoReturn
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from taskflow_api.core.config import settings
from taskflow_api.db.models.user import User
from taskflow_api.dependencies.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def raise_invalid_token() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Access token is not valid",
    )


def get_current_user(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    try:
        payload = jwt.decode(
            access_token,
            key=settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.InvalidTokenError:
        raise_invalid_token()

    user_id_raw = payload.get("sub")
    if not user_id_raw:
        raise_invalid_token()

    try:
        user_id = UUID(user_id_raw)
    except ValueError:
        raise_invalid_token()

    current_user: User | None = db.scalar(select(User).where(User.id == user_id))
    if not current_user:
        raise_invalid_token()

    return current_user
