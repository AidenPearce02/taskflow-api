from uuid import uuid4

from fastapi import status
from sqlalchemy import select

from taskflow_api.db.models.project import Project
from taskflow_api.db.models.project_member import ProjectMember, ProjectRole


def test_create_project(
    test_client,
    test_owner,
    test_project,
    create_user,
    auth_headers,
    create_project,
    test_db,
):
    owner = create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)

    project_data = create_project(test_project, owner_auth_headers)
    assert project_data["id"] is not None
    assert project_data["name"] == test_project["name"]
    assert project_data["description"] == test_project["description"]
    assert project_data["created_at"] is not None
    assert project_data["updated_at"] is not None

    project_id = project_data["id"]

    project: Project | None = test_db.scalar(
        select(Project).where(Project.id == project_id)
    )
    assert project is not None
    assert project.name == test_project["name"]
    assert project.description == test_project["description"]

    project_member: ProjectMember | None = test_db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id, ProjectMember.user_id == owner["id"]
        )
    )
    assert project_member is not None
    assert project_member.role == ProjectRole.OWNER


def test_create_project_without_token(test_client, test_project):
    response = test_client.post(
        "/projects",
        json=test_project,
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Not authenticated"


def test_create_project_without_name(
    test_client, test_owner, create_user, auth_headers, test_project
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)

    response = test_client.post(
        "/projects",
        json={"description": test_project["description"]},
        headers=owner_auth_headers,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_project_with_short_name(
    test_client, test_owner, create_user, auth_headers, test_project
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)

    response = test_client.post(
        "/projects",
        json={"name": "1", "description": test_project["description"]},
        headers=owner_auth_headers,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_get_projects(
    test_client, test_owner, test_project, create_user, auth_headers, create_project
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)

    response = test_client.get("/projects", headers=owner_auth_headers)
    assert response.status_code == status.HTTP_200_OK

    assert project_data in response.json()


def test_get_projects_only_returns_current_users_projects(
    test_client,
    test_owner,
    test_member,
    test_project,
    create_user,
    auth_headers,
    create_project,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)

    create_user(test_member)
    second_owner_auth_headers = auth_headers(test_member)
    second_project_data = create_project(test_project, second_owner_auth_headers)

    response = test_client.get("/projects", headers=second_owner_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert project_data not in response.json()
    assert second_project_data in response.json()


def test_get_empty_projects(test_client, test_owner, create_user, auth_headers):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    response = test_client.get("/projects", headers=owner_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_get_project(
    test_client, test_owner, test_project, create_user, auth_headers, create_project
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)

    response = test_client.get(
        f"/projects/{project_data['id']}", headers=owner_auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == project_data


def test_get_project_not_accessible_by_non_member(
    test_client,
    test_owner,
    test_member,
    test_project,
    create_user,
    auth_headers,
    create_project,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)

    create_user(test_member)
    non_member_auth_headers = auth_headers(test_member)
    response = test_client.get(
        f"/projects/{project_data['id']}", headers=non_member_auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project doesn't exist"


def test_get_nonexistent_project(test_client, test_owner, create_user, auth_headers):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)

    response = test_client.get(f"/projects/{uuid4()}", headers=owner_auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project doesn't exist"


def test_update_project(
    test_client,
    test_owner,
    test_project,
    create_user,
    auth_headers,
    create_project,
    test_db,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)

    new_name = "The best project ever"
    response = test_client.patch(
        f"/projects/{project_data['id']}",
        headers=owner_auth_headers,
        json={"name": new_name},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] != project_data["name"]
    assert response.json()["name"] == new_name

    project: Project | None = test_db.scalar(
        select(Project).where(Project.id == project_data["id"])
    )
    assert project is not None
    assert project.name == new_name


def test_update_project_not_accessible_by_non_member(
    test_client,
    test_owner,
    test_member,
    test_project,
    create_user,
    auth_headers,
    create_project,
    test_db,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)

    create_user(test_member)
    non_member_auth_headers = auth_headers(test_member)

    new_name = "The best project ever"
    response = test_client.patch(
        f"/projects/{project_data['id']}",
        headers=non_member_auth_headers,
        json={"name": new_name},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project doesn't exist"

    project: Project | None = test_db.scalar(
        select(Project).where(Project.id == project_data["id"])
    )
    assert project is not None
    assert project.name == project_data["name"]


def test_update_project_not_found(test_client, test_owner, create_user, auth_headers):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)

    new_name = "The best project ever"
    response = test_client.patch(
        f"/projects/{uuid4()}",
        headers=owner_auth_headers,
        json={"name": new_name},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project doesn't exist"


def test_delete_project(
    test_client,
    test_owner,
    test_project,
    create_user,
    auth_headers,
    create_project,
    test_db,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)

    response = test_client.delete(
        f"/projects/{project_data['id']}",
        headers=owner_auth_headers,
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    project: Project | None = test_db.scalar(
        select(Project).where(Project.id == project_data["id"])
    )
    assert project is None


def test_delete_project_not_accessible_by_non_member(
    test_client,
    test_owner,
    test_member,
    test_project,
    create_user,
    auth_headers,
    create_project,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)

    create_user(test_member)
    non_member_auth_headers = auth_headers(test_member)

    response = test_client.delete(
        f"/projects/{project_data['id']}",
        headers=non_member_auth_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project doesn't exist"


def test_delete_project_not_found(
    test_client,
    test_owner,
    create_user,
    auth_headers,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)

    response = test_client.delete(
        f"/projects/{uuid4()}",
        headers=owner_auth_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project doesn't exist"
