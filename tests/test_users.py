import pytest
from tests.test_photos import get_auth_headers

def test_user_management_role_and_delete_rbac(client):
    # 1. Створюємо першого користувача (він за замовчуванням ADMIN)
    client.post("/api/auth/signup", json={"username": "main_admin", "email": "admin@test.com", "password": "password123"})
    admin_headers = get_auth_headers(client, "admin@test.com", "password123")

    # 2. Створюємо другого користувача (він буде USER)
    client.post("/api/auth/signup", json={"username": "victim_user", "email": "victim@test.com", "password": "password123"})
    user_headers = get_auth_headers(client, "victim@test.com", "password123")

    # 3. ТЗ: Звичайний користувач намагається змінити роль іншому -> 403 Forbidden
    response_user_patch = client.patch("/api/users/1/role", headers=user_headers, json={"role": "admin"})
    assert response_user_patch.status_code == 403

    # 4. ТЗ: Адмін успішно підвищує користувача до MODERATOR
    response_admin_patch = client.patch("/api/users/2/role", headers=admin_headers, json={"role": "moderator"})
    assert response_admin_patch.status_code == 200
    assert response_admin_patch.json()["role"] == "moderator"

    # 5. ТЗ: Звичайний користувач намагається видалити адміна -> 403 Forbidden
    response_user_delete = client.delete("/api/users/1", headers=user_headers)
    assert response_user_delete.status_code == 403

    # 6. ТЗ: Адмін успішно видаляє обліковий запис користувача -> 204 No Content
    response_admin_delete = client.delete("/api/users/2", headers=admin_headers)
    assert response_admin_delete.status_code == 204
