import pytest
from tests.test_photos import get_auth_headers

def test_user_profile_operations_and_admin_actions(client):
    # 1. Реєструємо першого (ADMIN) та другого (USER)
    client.post("/api/auth/signup", json={"username": "boss", "email": "boss@test.com", "password": "password123"})
    client.post("/api/auth/signup", json={"username": "user", "email": "user@test.com", "password": "password123"})
    
    admin_headers = get_auth_headers(client, "boss@test.com", "password123")
    user_headers = get_auth_headers(client, "user@test.com", "password123")

    # GET /users/me
    response = client.get("/api/users/me", headers=user_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "user"

    # PUT /users/me (Зміна імені)
    response = client.put("/api/users/me", headers=user_headers, json={"username": "user_updated"})
    assert response.status_code == 200

    # GET /users/{username} (Публічний профіль)
    response = client.get("/api/users/user_updated", headers=user_headers)
    assert response.status_code == 200
    assert "photos_count" in response.json()

    # GET /users/{username} - 404 Not Found
    response = client.get("/api/users/non_existing_user", headers=user_headers)
    assert response.status_code == 404

    # PATCH /users/{id}/role - Адмін намагається змінити роль самому собі -> 400
    response = client.patch("/api/users/1/role", headers=admin_headers, json={"role": "user"})
    assert response.status_code == 400

    # PATCH /users/{id}/ban - Адмін намагається забанити себе -> 400
    response = client.patch("/api/users/1/ban?is_active=false", headers=admin_headers)
    assert response.status_code == 400

    # PATCH /users/{id}/ban - Успішний бан юзера адміном
    response = client.patch("/api/users/2/ban?is_active=false", headers=admin_headers)
    assert response.status_code == 200

    # DELETE /users/{id} - Адмін намагається видалити себе -> 400
    response = client.delete("/api/users/1", headers=admin_headers)
    assert response.status_code == 400

    # DELETE /users/{id} - Видалення неіснуючого юзера -> 404
    response = client.delete("/api/users/999", headers=admin_headers)
    assert response.status_code == 404
