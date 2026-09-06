from unittest.mock import MagicMock
import pytest
from src.services.cloudinary import cloudinary_service
from src.database.models import User

@pytest.fixture(autouse=True)
def mock_cloudinary(monkeypatch):
    # Створюємо заглушку для Cloudinary, щоб тести не стукали в інтернет
    mock_upload = MagicMock(return_value={"secure_url": "https://fake-cloudinary/image.jpg", "public_id": "fake_id"})
    mock_destroy = MagicMock(return_value={"result": "ok"})
    
    monkeypatch.setattr(cloudinary_service, "upload_photo", mock_upload)
    monkeypatch.setattr(cloudinary_service, "delete_photo", mock_destroy)
    monkeypatch.setattr(cloudinary_service, "get_transformed_url", lambda pid, pr: "https://fake-cloudinary/transformed.jpg")

def get_auth_headers(client, email, password):
    # Допоміжна функція для швидкого отримання токена авторизації
    response = client.post("/api/auth/login", data={"username": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_create_and_search_photo(client):
    # 1. Реєструємо першого адміна та отримуємо заголовки авторизації
    client.post("/api/auth/signup", json={"username": "admin", "email": "admin@example.com", "password": "password123"})
    headers = get_auth_headers(client, "admin@example.com", "password123")

    # 2. Тестуємо завантаження фотографії з описом та тегами
    # Використовуємо псевдо-файл для імітації завантаження через Form Data
    file_data = {"file": ("test.jpg", b"fake_bytes", "image/jpeg")}
    form_data = {"description": "Amazing summer beach", "tags": "summer, beach, nature"}
    
    response = client.post("/api/photos/", headers=headers, files=file_data, data=form_data)
    assert response.status_code == 201
    photo_data = response.json()
    assert photo_data["description"] == "Amazing summer beach"
    assert len(photo_data["tags"]) == 3

    # 3. Тестуємо наш розширений пошук (Блок зі смоук-тестування)
    search_response = client.get("/api/search/photos?keyword=beach&sort_by=date&order=desc", headers=headers)
    assert search_response.status_code == 200
    results = search_response.json()
    assert len(results) == 1
    assert results[0]["description"] == "Amazing summer beach"


def test_create_photo_tags_limit_error(client):
    client.post("/api/auth/signup", json={"username": "admin", "email": "admin@example.com", "password": "password123"})
    headers = get_auth_headers(client, "admin@example.com", "password123")

    # Передаємо більше ніж 5 тегів, система має повернути 400 Bad Request за ТЗ
    file_data = {"file": ("test.jpg", b"fake_bytes", "image/jpeg")}
    form_data = {"description": "Too many tags", "tags": "t1, t2, t3, t4, t5, t6"}
    
    response = client.post("/api/photos/", headers=headers, files=file_data, data=form_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "You can add a maximum of 5 tags to a photo."


def test_transform_photo_success(client):
    client.post("/api/auth/signup", json={"username": "admin", "email": "admin@example.com", "password": "password123"})
    headers = get_auth_headers(client, "admin@example.com", "password123")

    # Спочатку завантажуємо базове фото
    file_data = {"file": ("test.jpg", b"fake_bytes", "image/jpeg")}
    photo_resp = client.post("/api/photos/", headers=headers, files=file_data, data={"description": "Original"})
    photo_id = photo_resp.json()["id"]

    # Викликаємо ендпоінт трансформації та генерації QR-коду
    response = client.post(f"/api/photos/{photo_id}/transform", headers=headers, json={"preset": "black_white"})
    assert response.status_code == 201
    data = response.json()
    assert "transformed_url" in data
    assert "qr_code_url" in data
    
def test_photo_sad_paths_and_transformations(client):
    client.post("/api/auth/signup", json={"username": "photographer", "email": "photo@test.com", "password": "password"})
    headers = get_auth_headers(client, "photo@test.com", "password")

    # PUT /photos/{id} - Оновлення опису неіснуючого фото -> 404
    response = client.put("/api/photos/999", headers=headers, json={"description": "New"})
    assert response.status_code == 404

    # GET /photos/{id} - Отримання неіснуючого фото -> 404
    response = client.get("/api/photos/999", headers=headers)
    assert response.status_code == 404

    # DELETE /photos/{id} - Видалення неіснуючого фото -> 404
    response = client.delete("/api/photos/999", headers=headers)
    assert response.status_code == 404

    # POST /photos/{id}/transform - Трансформація неіснуючого фото -> 404
    response = client.post("/api/photos/999/transform", headers=headers, json={"preset": "avatar"})
    assert response.status_code == 404

