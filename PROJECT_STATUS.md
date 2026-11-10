# TaskFlow API — Project Status

**Last updated:** 2026-11-10  
**Project status:** Active development  
**Current milestone:** Task listing, filtering and pagination

## 1. Project Overview

TaskFlow is a multi-user REST API for project and task management, conceptually similar to a simplified Jira or Trello.

The primary goal is to build a production-oriented backend portfolio project demonstrating middle-level backend engineering skills.

The project emphasizes:
- Clean and maintainable architecture.
- Authentication and authorization.
- Database design and integrity.
- API validation and consistent error handling.
- Meaningful automated tests.
- Containerization and deployment readiness.

The project should remain reasonably scoped. Avoid adding features without a clear practical purpose.

## 2. Technology Stack

- Python 3.13
- FastAPI
- PostgreSQL 16
- SQLAlchemy 2.x (synchronous ORM)
- Alembic
- Pydantic / pydantic-settings
- JWT authentication
- pwdlib for password hashing
- Docker and Docker Compose
- pytest
- uv for dependency management
- Ruff for linting and formatting

## 3. Current Architecture

The application follows a modular structure under `src/taskflow_api`.

Main areas:
- `api/` — API routes and schemas.
- `db/` — database configuration and ORM models.
- `core/` — application configuration and shared functionality.

Database migrations are managed through Alembic.

The application uses SQLAlchemy ORM models and Pydantic schemas for request validation and response serialization.

The exact implementation should always be verified against the current source code.

## 4. Implemented Functionality

### Authentication and Users
- User registration.
- Password hashing.
- JWT access-token generation.
- JWT authentication dependency.
- Current-user endpoint (`/me`).
- Duplicate email validation.
- Invalid token handling.

### Projects
- Project creation and management.
- Project membership.
- Project roles:
  - `owner`
  - `admin`
  - `member`
- Role-based membership management.
- Access restricted to project members.

### Tasks

Implemented:
- Task creation.
- Task listing within a project.
- Pagination.
- Filtering by status.
- Filtering by priority.
- Filtering by assignee.
- Stable ordering by `created_at DESC, id DESC`.

Task fields:
- `id`
- `project_id`
- `title`
- `description`
- `status`
- `priority`
- `assignee_id`
- `due_date`
- `created_at`
- `updated_at`

Task statuses:
- `todo`
- `in_progress`
- `done`

Task priorities:
- `low`
- `medium`
- `high`

## 5. Important Business Rules

### Project Access
- Only project members can access project tasks.
- A non-member receives `404 Project doesn't exist`.
- This intentionally avoids revealing whether a project exists to unauthorized users.

### Task Creation
- Any project member can create a task.
- The default task status is `todo`.
- The default task priority is `medium`.
- The assignee is optional.
- An assignee must be a member of the same project.

### Task Listing
Endpoint:

`GET /projects/{project_id}/tasks`

Supported query parameters:

| Parameter | Description | Default |
|---|---|---|
| `status` | Filter by task status | None |
| `priority` | Filter by priority | None |
| `assignee_id` | Filter by assignee UUID | None |
| `page` | Page number, minimum 1 | 1 |
| `limit` | Items per page, 1–100 | 20 |

Multiple filters are combined using `AND`.

The response contains:
- `items`
- `total`
- `page`
- `limit`
- `pages`

Both the task query and count query use the same filter conditions. Therefore, `total` represents the number of matching tasks, not all tasks in the project.

An empty result returns an empty `items` list and `pages = 0` when no matching tasks exist.

## 6. Database Models

Existing models include:
- `User`
- `Project`
- `ProjectMember`
- `Task`

Important relationships:
- `Project.tasks` ↔ `Task.project`
- `User.assigned_tasks` ↔ `Task.assignee`
- Project membership connects users and projects.

The task table uses:
- UUID primary keys.
- Foreign keys to projects and users.
- `ON DELETE CASCADE` for project deletion.
- Non-null status and priority fields.
- Timezone-aware datetime columns.

Alembic migrations are used for schema changes.

## 7. Testing

The project uses pytest and FastAPI TestClient.

Existing tests cover:
- Authentication.
- User registration and login.
- Project operations.
- Membership and authorization.
- Task creation.
- Task creation with and without an assignee.
- Rejection of non-member task creation.
- Rejection of non-member assignees.
- Task listing by project member.
- Project data isolation.
- Pagination.
- Invalid pagination parameters.
- Task filtering by status, priority and assignee.
- Combined filters.
- Filtered `total` count.

The filtering tests include the empty-result case for `status=in_progress`, since newly created tasks default to `todo`.

Tests should verify meaningful behavior and edge cases without creating redundant test cases for every trivial variation.

## 8. Current Development Status

The current milestone is almost complete.

Implemented in the task listing endpoint:
- Pagination using `page` and `limit`.
- Filtering by `status`.
- Filtering by `priority`.
- Filtering by `assignee_id`.
- Consistent filtered count.
- Stable sorting.

The latest filtering test checks:
- `status=todo`
- `priority=medium`
- `assignee_id`
- Combined `status=todo&priority=low`
- Empty results using `status=in_progress`

The next step is to finish reviewing and running the tests for this milestone.

## 9. Recommended Next Steps

Suggested development order:

1. Finish and run the task filtering tests.
2. Implement task sorting:
   - Sort field, for example `created_at`, `due_date`, `priority`.
   - Sort direction: ascending or descending.
   - Validate supported sort fields and directions.
3. Implement task detail retrieval (`GET /projects/{project_id}/tasks/{task_id}`).
4. Implement task updates (`PATCH`).
   - Partial updates.
   - Revalidate assignee project membership when `assignee_id` changes.
   - Handle status and priority updates.
   - Update `updated_at`.
5. Implement task deletion.
6. Review authorization rules across all task endpoints.
7. Improve database indexes based on actual query patterns.
8. Add further integration tests and edge cases.
9. Review production configuration, logging and deployment.

These are proposed steps, not requirements to implement everything immediately. Keep the project focused.

## 10. Development and Tooling Notes

- Use `uv run` for Python commands.
- Use Docker Compose for local services.
- PostgreSQL test database migrations may need to be applied explicitly.
- Ruff is used for linting and formatting.
- Tests should run against an isolated test database.
- Never commit `.env` files, passwords, JWT secrets or other credentials.

Example commands:

```bash
uv run pytest
uv run ruff check .
uv run ruff format .
```

Apply migrations:

```bash
docker compose exec api alembic upgrade head
```

## 11. Mentoring and Collaboration Guidelines

The developer has commercial backend experience and wants to strengthen independent engineering skills through this project.

When helping with TaskFlow:

- Work incrementally.
- Review the developer's implementation before proposing a replacement.
- Explain why a change is necessary.
- Discuss relevant trade-offs.
- Avoid unnecessary abstractions and overengineering.
- Do not generate large implementations unless explicitly requested.
- Prefer practical, production-relevant engineering decisions.
- Recommend a reasonable test scope.
- Preserve existing architecture unless there is a strong reason to change it.

The developer should write the code and understand the decisions behind it. The assistant should act as a senior reviewer and technical mentor, not simply generate the entire application.

---

**Important:** This document describes the project state as of 2026-11-10. Always verify implementation details against the latest repository contents before making code changes.