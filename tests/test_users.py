from unittest.mock import AsyncMock

import src.routes.users as users_route
from tests.test_photos import VALID_IMAGE_BYTES, get_auth_headers

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


def test_avatar_upload_validates_before_uploading_once(client, monkeypatch):
    client.post(
        "/api/auth/signup",
        json={"username": "avatar_user", "email": "avatar@example.com", "password": "password123"},
    )
    headers = get_auth_headers(client, "avatar@example.com", "password123")
    save_avatar = AsyncMock(return_value="https://fake-cloudinary/avatar.png")
    monkeypatch.setattr(users_route, "save_avatar_to_cloudinary", save_avatar)

    response = client.post(
        "/api/users/me/avatar",
        headers=headers,
        files={"file": ("avatar.png", VALID_IMAGE_BYTES, "image/png")},
    )

    assert response.status_code == 200
    assert response.json()["avatar_url"] == "https://fake-cloudinary/avatar.png"
    save_avatar.assert_awaited_once()


def test_avatar_upload_rejects_invalid_image_before_upload(client, monkeypatch):
    client.post(
        "/api/auth/signup",
        json={"username": "invalid_avatar", "email": "invalid-avatar@example.com", "password": "password123"},
    )
    headers = get_auth_headers(client, "invalid-avatar@example.com", "password123")
    save_avatar = AsyncMock(return_value="https://fake-cloudinary/avatar.png")
    monkeypatch.setattr(users_route, "save_avatar_to_cloudinary", save_avatar)

    response = client.post(
        "/api/users/me/avatar",
        headers=headers,
        files={"file": ("avatar.png", b"not-an-image", "image/png")},
    )

    assert response.status_code == 400
    save_avatar.assert_not_awaited()
