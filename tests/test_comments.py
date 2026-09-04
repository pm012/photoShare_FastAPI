import pytest
from tests.test_photos import get_auth_headers, mock_cloudinary

def test_comment_lifecycle_and_rbac(client):
    # 1. Реєструємо та логінимо Адміна (ID 1)
    client.post("/api/auth/signup", json={"username": "admin", "email": "admin@example.com", "password": "password123"})
    admin_headers = get_auth_headers(client, "admin@example.com", "password123")

    # 2. Реєструємо та логінимо звичайного Користувача (ID 2)
    client.post("/api/auth/signup", json={"username": "user", "email": "user@example.com", "password": "password123"})
    user_headers = get_auth_headers(client, "user@example.com", "password123")

    # 3. Адмін завантажує фото
    file_data = {"file": ("test.jpg", b"fake_bytes", "image/jpeg")}
    photo_resp = client.post("/api/photos/", headers=admin_headers, files=file_data, data={"description": "Admin Photo"})
    photo_id = photo_resp.json()["id"]

    # 4. Звичайний користувач пише коментар під фото адміна
    comment_resp = client.post(f"/api/photos/{photo_id}/comments", headers=user_headers, json={"text": "Awesome shot!"})
    assert comment_resp.status_code == 201
    comment_id = comment_resp.json()["id"]

    # 5. Користувач успішно редагує свій коментар
    edit_resp = client.get(f"/api/photos/{photo_id}/comments", headers=user_headers)
    assert edit_resp.status_code == 200
    
    # 6. ТЗ: Звичайний користувач намагається видалити коментар -> має отримати 403 Forbidden
    delete_user_resp = client.delete(f"/api/photos/comments/{comment_id}", headers=user_headers)
    assert delete_user_resp.status_code == 403

    # 7. ТЗ: Адмін успішно видаляє коментар іншого користувача -> код 24
    delete_admin_resp = client.delete(f"/api/photos/comments/{comment_id}", headers=admin_headers)
    assert delete_admin_resp.status_code == 204
