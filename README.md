docker compose exec api alembic current
docker compose exec api alembic revision --autogenerate -m "create users table"
docker compose exec api alembic upgrade head

docker compose exec db psql -U <POSTGRES_USER> -d <POSTGRES_DB>

For tests:
docker compose exec db psql -U <POSTGRES_USER> -d <POSTGRES_DB>
CREATE DATABASE taskflow_test;
docker compose exec -e POSTGRES_DB=taskflow_test api alembic upgrade head;

To test: uv run pytest -v -s -k
v - verbose
s - to show prints
k - for test that contains name keyword