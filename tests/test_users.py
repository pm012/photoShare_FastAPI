from tests.test_photos import get_auth_headers

def test_user_profile_operations_and_admin_actions(client):
    # 1. Register the first (ADMIN) and second (USER)
    client.post("/api/auth/signup", json={"username": "boss", "email": "boss@test.com", "password": "password123"})
    client.post("/api/auth/signup", json={"username": "user", "email": "user@test.com", "password": "password123"})
    
    admin_headers = get_auth_headers(client, "boss@test.com", "password123")
    user_headers = get_auth_headers(client, "user@test.com", "password123")

    # GET /users/me
    response = client.get("/api/users/me", headers=user_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "user"

    # PUT /users/me (Changing the name)
    response = client.put("/api/users/me", headers=user_headers, json={"username": "user_updated"})
    assert response.status_code == 200

    # GET /users/{username} (Public profile)
    response = client.get("/api/users/user_updated", headers=user_headers)
    assert response.status_code == 200
    assert "photos_count" in response.json()

    # GET /users/{username} - 404 Not Found
    response = client.get("/api/users/non_existing_user", headers=user_headers)
    assert response.status_code == 404

    # PATCH /users/{id}/role - Admin tries to change their own role -> 400
    response = client.patch("/api/users/1/role", headers=admin_headers, json={"role": "user"})
    assert response.status_code == 400

    # PATCH /users/{id}/ban - Admin tries to ban themselves -> 400
    response = client.patch("/api/users/1/ban?is_active=false", headers=admin_headers)
    assert response.status_code == 400

    # PATCH /users/{id}/ban - Successful ban of user by admin
    response = client.patch("/api/users/2/ban?is_active=false", headers=admin_headers)
    assert response.status_code == 200

    # DELETE /users/{id} - Admin tries to delete themselves -> 400
    response = client.delete("/api/users/1", headers=admin_headers)
    assert response.status_code == 400

    # DELETE /users/{id} - Deleting a non-existing user -> 404
    response = client.delete("/api/users/999", headers=admin_headers)
    assert response.status_code == 404


def test_duplicate_username_is_rejected(client):
    client.post(
        "/api/auth/signup",
        json={"username": "same_name", "email": "first@example.com", "password": "password123"},
    )
    response = client.post(
        "/api/auth/signup",
        json={"username": "same_name", "email": "second@example.com", "password": "password123"},
    )
    assert response.status_code == 409


def test_duplicate_username_update_is_rejected(client):
    client.post(
        "/api/auth/signup",
        json={"username": "first", "email": "first@example.com", "password": "password123"},
    )
    client.post(
        "/api/auth/signup",
        json={"username": "second", "email": "second@example.com", "password": "password123"},
    )
    headers = get_auth_headers(client, "second@example.com", "password123")
    response = client.put(
        "/api/users/me",
        headers=headers,
        json={"username": "first"},
    )
    assert response.status_code == 409
