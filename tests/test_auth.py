from fastapi import status


def test_login(test_client, test_owner):
    response = test_client.post("/users", json=test_owner)
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    user_id = data["id"]

    response = test_client.post(
        "/auth/login",
        data={
            "username": test_owner["email"],
            "password": test_owner["password"],
        },
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]

    response = test_client.get(
        "/users/me", headers={"Authorization": f"Bearer {data['access_token']}"}
    )
    assert response.status_code == status.HTTP_200_OK

    me_data = response.json()
    assert me_data["id"] == user_id


def test_login_with_wrong_password(test_client, test_owner):
    response = test_client.post("/users", json=test_owner)
    assert response.status_code == status.HTTP_201_CREATED

    response = test_client.post(
        "/auth/login",
        data={
            "username": test_owner["email"],
            "password": f"nonexistent_{test_owner['password']}",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid email or password"


def test_login_with_nonexistent_email(test_client, test_owner):
    response = test_client.post("/users", json=test_owner)
    assert response.status_code == status.HTTP_201_CREATED

    response = test_client.post(
        "/auth/login",
        data={
            "username": f"nonexistent_{test_owner['email']}",
            "password": test_owner["password"],
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid email or password"


def test_get_me_without_token(test_client):
    response = test_client.get("/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Not authenticated"


def test_get_me_with_invalid_token(test_client, test_owner):
    response = test_client.post("/users", json=test_owner)
    assert response.status_code == status.HTTP_201_CREATED

    response = test_client.post(
        "/auth/login",
        data={
            "username": test_owner["email"],
            "password": test_owner["password"],
        },
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]

    response = test_client.get(
        "/users/me", headers={"Authorization": f"Bearer {data['access_token']}t"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Access token is not valid"
