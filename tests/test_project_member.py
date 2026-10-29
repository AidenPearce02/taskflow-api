from uuid import UUID

from fastapi import status
from sqlalchemy import select

from taskflow_api.db.models.project_member import ProjectMember, ProjectRole


def test_add_members_owner(
    test_client,
    test_owner,
    test_member,
    test_member2,
    test_project,
    create_user,
    auth_headers,
    create_project,
    add_member,
    test_db,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)

    create_user(test_member)
    create_user(test_member2)

    admin_membership = add_member(
        project_data["id"], test_member["email"], ProjectRole.ADMIN, owner_auth_headers
    )
    assert admin_membership["role"] == ProjectRole.ADMIN
    member_membership = add_member(
        project_data["id"],
        test_member2["email"],
        ProjectRole.MEMBER,
        owner_auth_headers,
    )
    assert member_membership["role"] == ProjectRole.MEMBER

    project_members: list[ProjectMember] = test_db.scalars(
        select(ProjectMember).where(ProjectMember.project_id == project_data["id"])
    ).all()
    assert any(
        member.user_id == UUID(admin_membership["user_id"])
        and member.role == ProjectRole.ADMIN
        for member in project_members
    )
    assert any(
        member.user_id == UUID(member_membership["user_id"])
        and member.role == ProjectRole.MEMBER
        for member in project_members
    )


def test_add_members_admin(
    test_client,
    test_owner,
    test_member,
    test_member2,
    test_project,
    create_user,
    auth_headers,
    create_project,
    add_member,
    test_db,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)

    create_user(test_member)
    admin_auth_headers = auth_headers(test_member)
    create_user(test_member2)

    add_member(
        project_data["id"], test_member["email"], ProjectRole.ADMIN, owner_auth_headers
    )

    member_membership = add_member(
        project_data["id"],
        test_member2["email"],
        ProjectRole.MEMBER,
        admin_auth_headers,
    )
    assert member_membership["role"] == ProjectRole.MEMBER

    project_members: list[ProjectMember] = test_db.scalars(
        select(ProjectMember).where(ProjectMember.project_id == project_data["id"])
    ).all()
    assert any(
        member.user_id == UUID(member_membership["user_id"])
        and member.role == ProjectRole.MEMBER
        for member in project_members
    )


def test_add_admin_by_admin_forbidden(
    test_client,
    test_owner,
    test_member,
    test_member2,
    test_project,
    create_user,
    auth_headers,
    create_project,
    add_member,
    test_db,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)

    create_user(test_member)
    admin_auth_headers = auth_headers(test_member)
    forbidden_admin = create_user(test_member2)

    add_member(
        project_data["id"], test_member["email"], ProjectRole.ADMIN, owner_auth_headers
    )

    response = test_client.post(
        f"/projects/{project_data['id']}/members",
        json={"email": test_member2["email"], "role": ProjectRole.ADMIN},
        headers=admin_auth_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Insufficient permissions"

    project_members: list[ProjectMember] = test_db.scalars(
        select(ProjectMember).where(ProjectMember.project_id == project_data["id"])
    ).all()
    assert not any(
        member.user_id == UUID(forbidden_admin["id"]) for member in project_members
    )


def test_add_admin_by_member_forbidden(
    test_client,
    test_owner,
    test_member,
    test_member2,
    test_project,
    create_user,
    auth_headers,
    create_project,
    add_member,
    test_db,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)

    create_user(test_member)
    member_auth_headers = auth_headers(test_member)
    forbidden_member = create_user(test_member2)

    add_member(
        project_data["id"], test_member["email"], ProjectRole.MEMBER, owner_auth_headers
    )

    response = test_client.post(
        f"/projects/{project_data['id']}/members",
        json={"email": test_member2["email"], "role": ProjectRole.ADMIN},
        headers=member_auth_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Insufficient permissions"

    project_members: list[ProjectMember] = test_db.scalars(
        select(ProjectMember).where(ProjectMember.project_id == project_data["id"])
    ).all()
    assert not any(
        member.user_id == UUID(forbidden_member["id"]) for member in project_members
    )


def test_add_member_by_member_forbidden(
    test_client,
    test_owner,
    test_member,
    test_member2,
    test_project,
    create_user,
    auth_headers,
    create_project,
    add_member,
    test_db,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)

    create_user(test_member)
    member_auth_headers = auth_headers(test_member)
    forbidden_member = create_user(test_member2)

    add_member(
        project_data["id"], test_member["email"], ProjectRole.MEMBER, owner_auth_headers
    )

    response = test_client.post(
        f"/projects/{project_data['id']}/members",
        json={"email": test_member2["email"], "role": ProjectRole.MEMBER},
        headers=member_auth_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Insufficient permissions"

    project_members: list[ProjectMember] = test_db.scalars(
        select(ProjectMember).where(ProjectMember.project_id == project_data["id"])
    ).all()
    assert not any(
        member.user_id == UUID(forbidden_member["id"]) for member in project_members
    )


def test_get_members_by_owner(
    test_client,
    test_owner,
    test_project,
    create_user,
    auth_headers,
    create_project,
):
    owner = create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)

    response = test_client.get(
        f"/projects/{project_data['id']}/members", headers=owner_auth_headers
    )
    assert response.status_code == status.HTTP_200_OK

    project_members: list[ProjectMember] = response.json()
    assert any(
        member["user_id"] == owner["id"] and member["role"] == ProjectRole.OWNER
        for member in project_members
    )


def test_get_members_by_admin(
    test_client,
    test_owner,
    test_member,
    test_project,
    create_user,
    auth_headers,
    create_project,
    add_member,
):
    owner = create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)

    admin = create_user(test_member)
    admin_auth_headers = auth_headers(test_member)

    add_member(
        project_data["id"], test_member["email"], ProjectRole.ADMIN, owner_auth_headers
    )

    response = test_client.get(
        f"/projects/{project_data['id']}/members", headers=admin_auth_headers
    )
    assert response.status_code == status.HTTP_200_OK

    project_members: list[ProjectMember] = response.json()
    assert any(
        member["user_id"] == owner["id"] and member["role"] == ProjectRole.OWNER
        for member in project_members
    )
    assert any(
        member["user_id"] == admin["id"] and member["role"] == ProjectRole.ADMIN
        for member in project_members
    )


def test_get_members_by_member(
    test_client,
    test_owner,
    test_member,
    test_project,
    create_user,
    auth_headers,
    create_project,
    add_member,
):
    owner = create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)

    user = create_user(test_member)
    member_auth_headers = auth_headers(test_member)

    add_member(
        project_data["id"], test_member["email"], ProjectRole.MEMBER, owner_auth_headers
    )

    response = test_client.get(
        f"/projects/{project_data['id']}/members", headers=member_auth_headers
    )
    assert response.status_code == status.HTTP_200_OK

    project_members: list[ProjectMember] = response.json()
    assert any(
        member["user_id"] == owner["id"] and member["role"] == ProjectRole.OWNER
        for member in project_members
    )
    assert any(
        member["user_id"] == user["id"] and member["role"] == ProjectRole.MEMBER
        for member in project_members
    )


def test_get_members_by_non_member(
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
        f"/projects/{project_data['id']}/members", headers=non_member_auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project doesn't exist"


def test_change_member_to_admin_by_owner(
    test_client,
    test_owner,
    test_member,
    test_project,
    create_user,
    auth_headers,
    create_project,
    add_member,
    test_db,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)

    create_user(test_member)

    user_membership = add_member(
        project_data["id"], test_member["email"], ProjectRole.MEMBER, owner_auth_headers
    )

    response = test_client.patch(
        f"/projects/{project_data['id']}/members/{user_membership['user_id']}",
        json={"role": ProjectRole.ADMIN},
        headers=owner_auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK

    updated_user_membership = response.json()
    assert updated_user_membership["role"] == ProjectRole.ADMIN

    membership: ProjectMember | None = test_db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_data["id"],
            ProjectMember.user_id == user_membership["user_id"],
        )
    )
    assert membership is not None
    assert membership.role == ProjectRole.ADMIN


def test_change_admin_to_member_by_owner(
    test_client,
    test_owner,
    test_member,
    test_project,
    create_user,
    auth_headers,
    create_project,
    add_member,
    test_db,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)

    create_user(test_member)

    user_membership = add_member(
        project_data["id"], test_member["email"], ProjectRole.ADMIN, owner_auth_headers
    )

    response = test_client.patch(
        f"/projects/{project_data['id']}/members/{user_membership['user_id']}",
        json={"role": ProjectRole.MEMBER},
        headers=owner_auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK

    updated_user_membership = response.json()
    assert updated_user_membership["role"] == ProjectRole.MEMBER

    membership: ProjectMember | None = test_db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_data["id"],
            ProjectMember.user_id == user_membership["user_id"],
        )
    )
    assert membership is not None
    assert membership.role == ProjectRole.MEMBER


def test_change_own_role_forbidden(
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

    response = test_client.patch(
        f"/projects/{project_data['id']}/members/{owner['id']}",
        json={"role": ProjectRole.ADMIN},
        headers=owner_auth_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Can't change your own role"

    membership: ProjectMember | None = test_db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_data["id"],
            ProjectMember.user_id == owner["id"],
        )
    )
    assert membership is not None
    assert membership.role == ProjectRole.OWNER


def test_change_to_same_role_forbidden(
    test_client,
    test_owner,
    test_member,
    test_project,
    create_user,
    auth_headers,
    create_project,
    add_member,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)

    create_user(test_member)

    user_membership = add_member(
        project_data["id"], test_member["email"], ProjectRole.ADMIN, owner_auth_headers
    )
    response = test_client.patch(
        f"/projects/{project_data['id']}/members/{user_membership['user_id']}",
        json={"role": ProjectRole.ADMIN},
        headers=owner_auth_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Member already has this role"


def test_change_member_to_admin_by_admin_forbidden(
    test_client,
    test_owner,
    test_member,
    test_member2,
    test_project,
    create_user,
    auth_headers,
    create_project,
    add_member,
    test_db,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)

    create_user(test_member)
    admin_auth_headers = auth_headers(test_member)
    create_user(test_member2)

    add_member(
        project_data["id"], test_member["email"], ProjectRole.ADMIN, owner_auth_headers
    )
    user_membership = add_member(
        project_data["id"],
        test_member2["email"],
        ProjectRole.MEMBER,
        owner_auth_headers,
    )
    response = test_client.patch(
        f"/projects/{project_data['id']}/members/{user_membership['user_id']}",
        json={"role": ProjectRole.ADMIN},
        headers=admin_auth_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Insufficient permissions"

    membership: ProjectMember | None = test_db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_data["id"],
            ProjectMember.user_id == user_membership["user_id"],
        )
    )
    assert membership is not None
    assert membership.role == ProjectRole.MEMBER


def test_change_admin_to_member_by_admin_forbidden(
    test_client,
    test_owner,
    test_member,
    test_member2,
    test_project,
    create_user,
    auth_headers,
    create_project,
    add_member,
    test_db,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)

    create_user(test_member)
    admin_auth_headers = auth_headers(test_member)
    create_user(test_member2)

    add_member(
        project_data["id"], test_member["email"], ProjectRole.ADMIN, owner_auth_headers
    )
    user_membership = add_member(
        project_data["id"],
        test_member2["email"],
        ProjectRole.ADMIN,
        owner_auth_headers,
    )
    response = test_client.patch(
        f"/projects/{project_data['id']}/members/{user_membership['user_id']}",
        json={"role": ProjectRole.MEMBER},
        headers=admin_auth_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Insufficient permissions"

    membership: ProjectMember | None = test_db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_data["id"],
            ProjectMember.user_id == user_membership["user_id"],
        )
    )
    assert membership is not None
    assert membership.role == ProjectRole.ADMIN


def test_change_someone_elses_role_by_member(
    test_client,
    test_owner,
    test_member,
    test_member2,
    test_project,
    create_user,
    auth_headers,
    create_project,
    add_member,
    test_db,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)

    create_user(test_member)
    member_auth_headers = auth_headers(test_member)
    create_user(test_member2)
    add_member(
        project_data["id"], test_member["email"], ProjectRole.MEMBER, owner_auth_headers
    )
    user_membership = add_member(
        project_data["id"],
        test_member2["email"],
        ProjectRole.MEMBER,
        owner_auth_headers,
    )
    response = test_client.patch(
        f"/projects/{project_data['id']}/members/{user_membership['user_id']}",
        json={"role": ProjectRole.MEMBER},
        headers=member_auth_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Insufficient permissions"

    membership: ProjectMember | None = test_db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_data["id"],
            ProjectMember.user_id == user_membership["user_id"],
        )
    )
    assert membership is not None
    assert membership.role == ProjectRole.MEMBER


def test_remove_member_by_owner(
    test_client,
    test_owner,
    test_member,
    test_project,
    create_user,
    auth_headers,
    create_project,
    add_member,
    test_db,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)

    create_user(test_member)
    user_membership = add_member(
        project_data["id"], test_member["email"], ProjectRole.MEMBER, owner_auth_headers
    )

    response = test_client.delete(
        f"/projects/{project_data['id']}/members/{user_membership['user_id']}",
        headers=owner_auth_headers,
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    membership: ProjectMember | None = test_db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_data["id"],
            ProjectMember.user_id == user_membership["user_id"],
        )
    )
    assert membership is None


def test_remove_own_membership_forbidden(
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

    response = test_client.delete(
        f"/projects/{project_data['id']}/members/{owner['id']}",
        headers=owner_auth_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Can't remove yourself from project"

    membership: ProjectMember | None = test_db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_data["id"],
            ProjectMember.user_id == owner["id"],
        )
    )

    assert membership is not None
    assert membership.role == ProjectRole.OWNER


def test_remove_admin_by_admin_forbidden(
    test_client,
    test_owner,
    test_member,
    test_member2,
    test_project,
    create_user,
    add_member,
    auth_headers,
    create_project,
    test_db,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)

    create_user(test_member)
    admin_auth_headers = auth_headers(test_member)
    create_user(test_member2)
    add_member(
        project_data["id"], test_member["email"], ProjectRole.ADMIN, owner_auth_headers
    )
    admin_membership = add_member(
        project_data["id"],
        test_member2["email"],
        ProjectRole.ADMIN,
        owner_auth_headers,
    )

    response = test_client.delete(
        f"/projects/{project_data['id']}/members/{admin_membership['user_id']}",
        headers=admin_auth_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Insufficient permissions"

    membership: ProjectMember | None = test_db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_data["id"],
            ProjectMember.user_id == admin_membership["user_id"],
        )
    )

    assert membership is not None
    assert membership.role == ProjectRole.ADMIN


def test_remove_member_by_admin(
    test_client,
    test_owner,
    test_member,
    test_member2,
    test_project,
    create_user,
    add_member,
    auth_headers,
    create_project,
    test_db,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)

    create_user(test_member)
    admin_auth_headers = auth_headers(test_member)
    create_user(test_member2)
    add_member(
        project_data["id"], test_member["email"], ProjectRole.ADMIN, owner_auth_headers
    )
    user_membership = add_member(
        project_data["id"],
        test_member2["email"],
        ProjectRole.MEMBER,
        owner_auth_headers,
    )

    response = test_client.delete(
        f"/projects/{project_data['id']}/members/{user_membership['user_id']}",
        headers=admin_auth_headers,
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    membership: ProjectMember | None = test_db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_data["id"],
            ProjectMember.user_id == user_membership["user_id"],
        )
    )
    assert membership is None


def test_remove_member_by_member_forbidden(
    test_client,
    test_owner,
    test_member,
    test_member2,
    test_project,
    create_user,
    add_member,
    auth_headers,
    create_project,
    test_db,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)

    create_user(test_member)
    member_auth_headers = auth_headers(test_member)
    create_user(test_member2)
    add_member(
        project_data["id"], test_member["email"], ProjectRole.MEMBER, owner_auth_headers
    )
    user_membership = add_member(
        project_data["id"],
        test_member2["email"],
        ProjectRole.MEMBER,
        owner_auth_headers,
    )

    response = test_client.delete(
        f"/projects/{project_data['id']}/members/{user_membership['user_id']}",
        headers=member_auth_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Insufficient permissions"

    membership: ProjectMember | None = test_db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_data["id"],
            ProjectMember.user_id == user_membership["user_id"],
        )
    )

    assert membership is not None
    assert membership.role == ProjectRole.MEMBER
