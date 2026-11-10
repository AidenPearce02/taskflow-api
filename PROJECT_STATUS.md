# TaskFlow API — Project Status

**Last updated:** 2026-11-10  
**Project status:** Active development  
**Current milestone:** Task listing, filtering and pagination — completed  
**Next milestone:** Configurable task sorting

## 1. Project Overview

TaskFlow is a multi-user REST API for project and task management, conceptually similar to a simplified Jira or Trello.

The goal is a maintainable backend portfolio project demonstrating middle-level engineering skills: authentication and authorization, relational data modeling, API validation, meaningful tests, and containerized development.

Keep the scope practical. Introduce additional layers or features only when they solve a concrete problem.

## 2. Technology Stack

- Python 3.13
- FastAPI
- PostgreSQL 16
- SQLAlchemy 2.x (synchronous ORM)
- Alembic
- Pydantic / pydantic-settings
- JWT authentication (PyJWT)
- pwdlib / Argon2 password hashing
- Docker / Docker Compose
- pytest and FastAPI TestClient
- uv for environment and dependency management
- Ruff configuration for linting and formatting (`.ruff.toml`)

## 3. Current Architecture

Application source is located in `src/taskflow_api/`:

- `api/routes/` — FastAPI endpoints and endpoint-level business logic.
- `api/schemas/` — Pydantic request/response contracts.
- `db/models/` — SQLAlchemy ORM models and relationships.
- `db/` — database base and connection/session configuration.
- `dependencies/` — database-session and authenticated-user dependencies.
- `core/` — configuration, password hashing and JWT helpers.
- `main.py` — FastAPI app, router registration and health endpoints.

There is **no separate service or repository layer**. Routes use synchronous SQLAlchemy `Session` objects via FastAPI dependencies. This is intentional at the current project scale; do not add abstraction layers without a demonstrated need.

Database schema changes are versioned with Alembic (three migrations).

## 4. Implemented Functionality

### Authentication and Users

- `POST /users` — registration, with password hashing and duplicate-email handling.
- `POST /auth/login` — login and JWT access-token issuance.
- `GET /users/me` — authenticated user profile.
- JWT authentication dependency, including rejection of invalid credentials/tokens.

### Projects

- `POST /projects` — create a project and assign the creator the `owner` role.
- `GET /projects` — list projects visible to the current user.
- `GET /projects/{project_id}` — project details.
- `PATCH /projects/{project_id}` — project update (owner/admin).
- `DELETE /projects/{project_id}` — project deletion (owner).
- Project member management: add, list, change role, remove.
- Project roles: `owner`, `admin`, `member`, with role-dependent operations.

### Tasks

- `POST /projects/{project_id}/tasks` — create a task.
- `GET /projects/{project_id}/tasks` — list tasks, with filtering and pagination.
- Fixed, deterministic ordering: `created_at DESC, id DESC`.

Task fields: `id`, `project_id`, `title`, `description`, `status`, `priority`, `assignee_id`, `due_date`, `created_at`, `updated_at`.

- Statuses: `todo`, `in_progress`, `done`.
- Priorities: `low`, `medium`, `high`.

### Health

- `GET /health` — application health endpoint.
- `GET /health/db` — database connectivity check.

**Not implemented yet:** configurable task sorting, task detail retrieval, task update and task deletion endpoints.

## 5. Important Business Rules

### Project Access

- Task creation/listing requires membership in the corresponding project.
- Non-members receive `404 Project doesn't exist`, intentionally avoiding project existence disclosure.
- Project update requires owner/admin; project deletion requires owner.
- Membership management follows the role-permission rules in `project_member.py`.

### Task Creation

- Any project member can create a task.
- Initial task status is `todo`; default priority is `medium`.
- `assignee_id` is optional.
- **At task creation time**, a non-null assignee must be a member of the same project.

Current limitation: removing a project member does not automatically clear task assignments referring to that user. Therefore the assignee-membership rule is validated on creation, but is not maintained as a permanent invariant after membership changes.

### Task Listing

`GET /projects/{project_id}/tasks`

| Parameter | Description | Default |
|---|---|---|
| `status` | Filter by task status | None |
| `priority` | Filter by priority | None |
| `assignee_id` | Filter by assignee UUID | None |
| `page` | Page number, minimum 1 | 1 |
| `limit` | Items per page, 1–100 | 20 |

Filters are combined with `AND`. The list and count queries use the same conditions, so `total` counts **matching tasks**, not all tasks in the project.

Response fields: `items`, `total`, `page`, `limit`, `pages`.

When no tasks match: `items = []`, `total = 0`, `pages = 0`. The endpoint uses a stable fixed order (`created_at DESC, id DESC`) before applying offset/limit pagination.

## 6. Database Models and Migrations

ORM models:

- `User`
- `Project`
- `ProjectMember` (user/project association with a role)
- `Task`

Notable relationships:

- `Project.tasks` ↔ `Task.project`.
- `User.assigned_tasks` ↔ `Task.assignee`.
- Project membership links users to projects.

Tasks use UUID primary keys, foreign keys to projects and users, non-null status/priority values, and timezone-aware datetime columns. Deleting a project cascades to its tasks at the database level.

Known migration follow-up: the task migration's `downgrade()` drops the table but does not explicitly drop PostgreSQL enum types `task_status` and `task_priority`. Consider this when reviewing downgrade/re-upgrade behavior; it is not part of the current sorting milestone.

## 7. Testing

The repository contains **60 test functions**, including **9 task tests**, using pytest and FastAPI TestClient.

Task tests cover:

- Task creation, including optional assignee and membership validation.
- Member access and separation between projects.
- Pagination and invalid pagination parameters.
- Filtering by status, priority and assignee.
- Combined status/priority filtering.
- Filtered `total` and empty-result responses, including `pages == 0` when no tasks match.

Test fixtures use a separate PostgreSQL database (`taskflow_test`) with transaction/savepoint isolation. The database must exist and have migrations applied.

**Verification status:** All 60 tests passed in the developer's local environment on 2026-11-10 (developer-confirmed). The suite was not independently re-run the run current code.

## 8. Current Development Status

The task-listing implementation already supports pagination, three filters, filtered counts and deterministic ordering.

The task-listing, filtering and pagination milestone is **complete**. The test suite passed locally (60 tests, developer-confirmed), and the empty-result `pages == 0` assertion is included in the current code.

The next incremental development step is configurable sorting for `GET /projects/{project_id}/tasks`. No configurable sort parameters are implemented yet.

## 9. Recommended Next Steps

In order:

1. Design configurable task sorting for `GET /projects/{project_id}/tasks`: supported fields, sort direction, validation, default behavior and deterministic pagination order.
2. Implement sorting in a small increment, following the existing endpoint architecture.
3. Add focused tests for supported/invalid sorting and stable ordering with pagination.
4. Implement task detail retrieval (`GET /projects/{project_id}/tasks/{task_id}`).
5. Implement partial task updates (`PATCH`), including relevant authorization and assignee-membership checks.
6. Implement task deletion and review permissions across task endpoints.
7. Address known integrity/migration limitations when their related workflows are revisited.
8. Review indexes, production configuration, logging and deployment based on actual needs.

These are milestones, not a requirement to build everything at once. Keep iterations small and review the existing code before introducing changes.

## 10. Development and Tooling Notes

- Use `uv` for Python dependency management and execution.
- Use Docker Compose for local application and PostgreSQL services.
- Use the isolated PostgreSQL test database for integration tests.
- Keep `.env`, passwords, JWT secrets and other credentials out of Git.
- `.ruff.toml` uses Python 3.13, a line length of 88, basic correctness/import rules and the Ruff formatter. Generated Alembic revision files are excluded from linting/formatting to avoid rewriting migration history.

Run tests:

```bash
uv run pytest tests/test_tasks.py -v
uv run pytest
```

Run Ruff:

```bash
uv run ruff check . --fix
uv run ruff format .
uv run ruff check .
uv run ruff format --check .
```

Apply migrations to the app database:

```bash
docker compose exec api alembic upgrade head
```

The isolated test database also requires migrations (with its own DB configuration).

## 11. Mentoring and Collaboration Guidelines

The developer has commercial backend experience and is building this project to strengthen independent engineering skills.

- Work in small, logical increments.
- Review the developer's code before offering rewritten solutions.
- Explain correctness issues, architectural trade-offs and alternatives.
- Avoid premature abstractions and unnecessary rewrites.
- Prefer tests that cover real behavior and failure cases.
- Respect the existing architecture and current scope.
- Let the developer implement features; act as reviewer and mentor.
