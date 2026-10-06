docker compose exec api alembic current
docker compose exec api alembic revision --autogenerate -m "create users table"
docker compose exec api alembic upgrade head

docker compose exec db psql -U <POSTGRES_USER> -d <POSTGRES_DB>