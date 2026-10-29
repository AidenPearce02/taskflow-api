from fastapi import status


def test_health(test_client):
    response = test_client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Healthy"}


def test_owner(test_owner):
    assert test_owner.get("email", "") == "owner@example.com"


def test_health_db(test_client):
    response = test_client.get("/health/db")

    assert response.status_code == status.HTTP_200_OK
