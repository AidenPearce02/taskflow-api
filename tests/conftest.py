from collections.abc import Callable, Iterator

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from taskflow_api.api.schemas.project import ProjectMemberResponse, ProjectResponse
from taskflow_api.api.schemas.user import UserResponse
from taskflow_api.core.config import settings
from taskflow_api.dependencies.database import get_db
from taskflow_api.main import app


@pytest.fixture
def test_client(test_db: Session) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[Session]:
        yield test_db

    previous_override = app.dependency_overrides.get(get_db)

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        if previous_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_override


@pytest.fixture(scope="session")
def test_engine() -> Iterator[Engine]:
    engine = create_engine(
        settings.db_url.set(database="taskflow_test", host="127.0.0.1"),
        pool_pre_ping=True,
    )
    yield engine
    engine.dispose()


@pytest.fixture
def test_owner() -> dict[str, str]:
    return {"email": "owner@example.com", "password": "string"}


@pytest.fixture
def test_member() -> dict[str, str]:
    return {
        "email": "member@example.com",
        "password": "member-password",
    }


@pytest.fixture
def test_member2() -> dict[str, str]:
    return {
        "email": "member2@example.com",
        "password": "member-password",
    }


@pytest.fixture
def test_project() -> dict[str, str]:
    return {"name": "TaskFlow", "description": "Some basic description"}


@pytest.fixture
def test_db(test_engine: Engine) -> Iterator[Session]:
    connection = test_engine.connect()
    transaction = connection.begin()

    db = Session(
        bind=connection, autoflush=False, join_transaction_mode="create_savepoint"
    )

    try:
        yield db
    finally:
        db.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def create_user(test_client: TestClient) -> Callable[[dict[str, str]], UserResponse]:
    def create(user_data: dict[str, str]) -> UserResponse:
        response = test_client.post("/users", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED

        return response.json()

    return create


@pytest.fixture
def auth_headers(test_client: TestClient) -> Callable[[dict[str, str]], dict[str, str]]:
    def get_headers(user_data: dict[str, str]) -> dict[str, str]:
        response = test_client.post(
            "/auth/login",
            data={
                "username": user_data["email"],
                "password": user_data["password"],
            },
        )
        assert response.status_code == status.HTTP_200_OK

        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return get_headers


@pytest.fixture
def create_project(
    test_client: TestClient,
) -> Callable[[dict[str, str], dict[str, str]], ProjectResponse]:
    def create(
        project_data: dict[str, str], headers: dict[str, str]
    ) -> ProjectResponse:
        response = test_client.post("/projects", json=project_data, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED

        return response.json()

    return create


@pytest.fixture
def add_member(
    test_client: TestClient,
) -> Callable[[str, str, str, dict[str, str]], ProjectMemberResponse]:
    def add(
        project_id: str, email: str, role: str, headers: dict[str, str]
    ) -> ProjectMemberResponse:
        response = test_client.post(
            f"/projects/{project_id}/members",
            json={"email": email, "role": role},
            headers=headers,
        )
        assert response.status_code == status.HTTP_201_CREATED

        return response.json()

    return add
