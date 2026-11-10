from datetime import datetime
from uuid import UUID

from fastapi import status
from sqlalchemy import select

from taskflow_api.db.models.project_member import ProjectRole
from taskflow_api.db.models.task import Task, TaskPriority, TaskStatus


def test_add_task_with_assignee(
    test_owner,
    test_member,
    test_project,
    test_task,
    create_user,
    auth_headers,
    create_project,
    create_task,
    add_member,
    test_db,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)
    project_id = project_data["id"]

    create_user(test_member)
    member_membership = add_member(
        project_id, test_member["email"], ProjectRole.MEMBER, owner_auth_headers
    )
    task_payload = {
        **test_task,
        "assignee_id": member_membership["user_id"],
    }

    task_data = create_task(project_data["id"], task_payload, owner_auth_headers)
    assert task_data["id"] is not None
    assert task_data["project_id"] == project_id
    assert task_data["title"] == task_payload["title"]
    assert task_data["description"] == task_payload["description"]
    assert task_data["status"] == TaskStatus.TODO
    assert task_data["priority"] == task_payload["priority"]
    assert task_data["assignee_id"] == member_membership["user_id"]
    assert task_data["due_date"] == task_payload["due_date"]
    assert task_data["created_at"] is not None
    assert task_data["updated_at"] is not None

    task_id = task_data["id"]

    task: Task | None = test_db.scalar(select(Task).where(Task.id == task_id))
    assert task is not None
    assert task.title == task_payload["title"]
    assert task.description == task_payload["description"]
    assert task.project_id == UUID(project_id)
    assert task.status == TaskStatus.TODO
    assert task.priority == task_payload["priority"]
    assert task.assignee_id == UUID(member_membership["user_id"])
    assert task.due_date == datetime.fromisoformat(task_payload["due_date"])


def test_add_task_without_assignee(
    test_client,
    test_owner,
    test_project,
    test_task,
    create_user,
    auth_headers,
    create_project,
    create_task,
    test_db,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)
    project_id = project_data["id"]

    task_payload = {
        **test_task,
    }
    task_data = create_task(project_data["id"], task_payload, owner_auth_headers)
    assert task_data["id"] is not None
    assert task_data["project_id"] == project_id
    assert task_data["title"] == task_payload["title"]
    assert task_data["description"] == task_payload["description"]
    assert task_data["status"] == TaskStatus.TODO
    assert task_data["priority"] == task_payload["priority"]
    assert task_data["assignee_id"] is None
    assert task_data["due_date"] == task_payload["due_date"]
    assert task_data["created_at"] is not None
    assert task_data["updated_at"] is not None

    task_id = task_data["id"]

    task: Task | None = test_db.scalar(select(Task).where(Task.id == task_id))
    assert task is not None
    assert task.title == task_payload["title"]
    assert task.description == task_payload["description"]
    assert task.project_id == UUID(project_id)
    assert task.status == TaskStatus.TODO
    assert task.priority == task_payload["priority"]
    assert task.assignee_id is None
    assert task.due_date == datetime.fromisoformat(task_payload["due_date"])


def test_add_task_by_non_member(
    test_client,
    test_owner,
    test_member,
    test_project,
    test_task,
    create_user,
    auth_headers,
    create_project,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)
    project_id = project_data["id"]

    create_user(test_member)
    not_member_auth_headers = auth_headers(test_member)

    task_payload = {
        **test_task,
    }

    response = test_client.post(
        f"/projects/{project_id}/tasks",
        json=task_payload,
        headers=not_member_auth_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project doesn't exist"


def test_add_task_with_non_member_assignee(
    test_client,
    test_owner,
    test_member,
    test_project,
    test_task,
    create_user,
    auth_headers,
    create_project,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)
    project_id = project_data["id"]

    not_member = create_user(test_member)

    task_payload = {
        **test_task,
        "assignee_id": not_member["id"],
    }

    response = test_client.post(
        f"/projects/{project_id}/tasks",
        json=task_payload,
        headers=owner_auth_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Assignee must be a member of the project"


def test_get_tasks_by_member(
    test_client,
    test_owner,
    test_member,
    test_project,
    test_task,
    create_task,
    create_user,
    auth_headers,
    add_member,
    create_project,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)
    project_id = project_data["id"]

    create_user(test_member)
    member_auth_headers = auth_headers(test_member)
    add_member(project_id, test_member["email"], ProjectRole.MEMBER, owner_auth_headers)
    tasks = []
    for i in range(4):
        task_payload = {**test_task, "title": f"task {i}"}
        tasks.append(create_task(project_id, task_payload, owner_auth_headers))
    tasks = sorted(tasks, key=lambda x: (x["created_at"], x["id"]), reverse=True)

    response = test_client.get(
        f"/projects/{project_id}/tasks", headers=member_auth_headers
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["items"] == tasks
    assert data["total"] == len(tasks)
    assert data["page"] == 1
    assert data["limit"] == 20
    assert data["pages"] == 1


def test_get_tasks_from_own_project_only(
    test_client,
    test_owner,
    test_member,
    test_project,
    test_task,
    create_task,
    create_user,
    auth_headers,
    add_member,
    create_project,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)
    project_id_1 = project_data["id"]
    project_data = create_project(test_project, owner_auth_headers)
    project_id_2 = project_data["id"]

    create_user(test_member)
    member_auth_headers = auth_headers(test_member)
    add_member(
        project_id_1, test_member["email"], ProjectRole.MEMBER, owner_auth_headers
    )

    task_payload = {**test_task}
    member_task = create_task(project_id_1, task_payload, owner_auth_headers)
    task_payload = {**test_task}
    create_task(project_id_2, task_payload, owner_auth_headers)

    response = test_client.get(
        f"/projects/{project_id_1}/tasks", headers=member_auth_headers
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["items"] == [member_task]
    assert data["total"] == len([member_task])
    assert data["page"] == 1
    assert data["limit"] == 20
    assert data["pages"] == 1

    response = test_client.get(
        f"/projects/{project_id_2}/tasks", headers=member_auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project doesn't exist"


def test_get_tasks_pagination(
    test_client,
    test_owner,
    test_project,
    test_task,
    create_task,
    create_user,
    auth_headers,
    create_project,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)
    project_id = project_data["id"]

    tasks = []
    for i in range(4):
        task_payload = {**test_task, "title": f"task {i}"}
        tasks.append(create_task(project_id, task_payload, owner_auth_headers))
    tasks = sorted(tasks, key=lambda x: (x["created_at"], x["id"]), reverse=True)

    response = test_client.get(
        f"/projects/{project_id}/tasks?page=1&limit=2", headers=owner_auth_headers
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["items"] == tasks[:2]
    assert data["total"] == len(tasks)
    assert data["page"] == 1
    assert data["limit"] == 2
    assert data["pages"] == 2

    response = test_client.get(
        f"/projects/{project_id}/tasks?page=2&limit=2", headers=owner_auth_headers
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["items"] == tasks[2:4]
    assert data["total"] == len(tasks)
    assert data["page"] == 2
    assert data["limit"] == 2
    assert data["pages"] == 2

    response = test_client.get(
        f"/projects/{project_id}/tasks?page=3&limit=2", headers=owner_auth_headers
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["items"] == []
    assert data["total"] == len(tasks)
    assert data["page"] == 3
    assert data["limit"] == 2
    assert data["pages"] == 2


def test_get_tasks_wrong_query_params(
    test_client,
    test_owner,
    test_project,
    create_user,
    auth_headers,
    create_project,
):
    create_user(test_owner)
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)
    project_id = project_data["id"]

    response = test_client.get(
        f"/projects/{project_id}/tasks?page=0", headers=owner_auth_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    response = test_client.get(
        f"/projects/{project_id}/tasks?limit=0", headers=owner_auth_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    response = test_client.get(
        f"/projects/{project_id}/tasks?limit=101", headers=owner_auth_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_get_tasks_with_filters(
    test_client,
    test_owner,
    test_project,
    test_task,
    create_user,
    create_task,
    create_project,
    auth_headers,
):
    owner = create_user(test_owner)
    user_id = owner["id"]
    owner_auth_headers = auth_headers(test_owner)
    project_data = create_project(test_project, owner_auth_headers)
    project_id = project_data["id"]

    tasks = []
    for _ in range(2):
        task_payload = {
            **test_task,
            "priority": TaskPriority.MEDIUM,
        }
        tasks.append(create_task(project_id, task_payload, owner_auth_headers))
    for _ in range(2):
        task_payload = {
            **test_task,
        }
        tasks.append(create_task(project_id, task_payload, owner_auth_headers))
    for _ in range(2):
        task_payload = {
            **test_task,
            "priority": TaskPriority.LOW,
            "assignee_id": user_id,
        }
        tasks.append(create_task(project_id, task_payload, owner_auth_headers))
    for _ in range(2):
        task_payload = {
            **test_task,
            "priority": TaskPriority.HIGH,
        }
        tasks.append(create_task(project_id, task_payload, owner_auth_headers))
    tasks = sorted(tasks, key=lambda x: (x["created_at"], x["id"]), reverse=True)

    response = test_client.get(
        f"/projects/{project_id}/tasks?status=todo", headers=owner_auth_headers
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["items"] == [t for t in tasks if t["status"] == TaskStatus.TODO]
    assert data["total"] == 8

    response = test_client.get(
        f"/projects/{project_id}/tasks?priority=medium", headers=owner_auth_headers
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["items"] == [t for t in tasks if t["priority"] == TaskPriority.MEDIUM]
    assert data["total"] == 4

    response = test_client.get(
        f"/projects/{project_id}/tasks?assignee_id={user_id}",
        headers=owner_auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["items"] == [t for t in tasks if t["assignee_id"] == user_id]
    assert data["total"] == 2

    response = test_client.get(
        f"/projects/{project_id}/tasks?status=todo&priority=low",
        headers=owner_auth_headers,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["items"] == [
        t
        for t in tasks
        if t["priority"] == TaskPriority.LOW and t["status"] == TaskStatus.TODO
    ]
    assert data["total"] == 2

    response = test_client.get(
        f"/projects/{project_id}/tasks?status=in_progress",
        headers=owner_auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["pages"] == 0
