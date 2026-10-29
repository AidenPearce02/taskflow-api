from fastapi import status
from sqlalchemy import select

from taskflow_api.core.security import verify_password
from taskflow_api.db.models.user import User


def test_create_user(test_client, test_db, test_owner):
    response = test_client.post("/users", json=test_owner)

    assert response.status_code == status.HTTP_201_CREATED

    user: User = test_db.scalar(select(User).where(User.email == test_owner["email"]))

    assert user is not None

    assert user.email == test_owner["email"]
    assert user.password_hash
    assert user.password_hash != test_owner["password"]
    assert verify_password(test_owner["password"], user.password_hash)

    data = response.json()
    assert data["id"] == str(user.id)
    assert data["created_at"] is not None
    assert "password" not in data
    assert "password_hash" not in data


def test_create_user_with_existing_email(test_client, test_owner):
    response = test_client.post("/users", json=test_owner)
    assert response.status_code == status.HTTP_201_CREATED

    response = test_client.post("/users", json=test_owner)

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Already created with this email"


def test_create_user_with_invalid_email(test_client, test_owner):
    user = {
        "email": test_owner["email"].replace("@", ""),
        "password": test_owner["password"],
    }
    response = test_client.post("/users", json=user)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_user_without_email(test_client, test_owner):
    response = test_client.post(
        "/users",
        json={"password": test_owner["password"]},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_user_without_password(test_client, test_owner):
    response = test_client.post(
        "/users",
        json={"email": test_owner["email"]},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_user_with_non_string_password(test_client, test_owner):
    response = test_client.post(
        "/users",
        json={
            "email": test_owner["email"],
            "password": 123456,
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
