import pytest
from src.database.models import Photo, Rating
from src.repository import ratings as repository_ratings

def test_full_ratings_lifecycle_and_constraints(client, db_session):
    # 1. Реєструємо трьох користувачів: Admin, Автор фото, Оцінювач
    client.post("/api/auth/signup", json={"username": "admin_v", "email": "admin@test.com", "password": "password123"})
    client.post("/api/auth/signup", json={"username": "author_v", "email": "author@test.com", "password": "password123"})
    client.post("/api/auth/signup", json={"username": "voter_v", "email": "voter@test.com", "password": "password123"})

    # Отримуємо заголовки для логіну
    def get_token(email):
        res = client.post("/api/auth/login", data={"username": email, "password": "password123"})
        return f"Bearer {res.json()['access_token']}"

    admin_token = get_token("admin@test.com")
    author_token = get_token("author@test.com")
    voter_token = get_token("voter@test.com")

    # 2. Створюємо фото прямо в тестовій базі через ORM, щоб уникнути помилки 500 від Cloudinary
    photo = Photo(user_id=2, url="https://fake-url.com", public_id="fake_123", description="Test Photo")
    db_session.add(photo)
    db_session.commit()
    db_session.refresh(photo)

    # 3. Автор намагається оцінити ВЛАСНЕ фото -> 400 Bad Request
    response = client.post(f"/api/photos/{photo.id}/rate", headers={"Authorization": author_token}, json={"rate": 5})
    assert response.status_code == 400

    # 4. Невалідна оцінка (6 зірок) -> 422 Unprocessable Entity (Pydantic Field валідація)
    response = client.post(f"/api/photos/{photo.id}/rate", headers={"Authorization": voter_token}, json={"rate": 6})
    assert response.status_code == 422

    # 5. Успішне виставлення оцінки (5 зірок) від іншого юзера
    response = client.post(f"/api/photos/{photo.id}/rate", headers={"Authorization": voter_token}, json={"rate": 5})
    assert response.status_code == 201

    # 6. Повторна оцінка від того самого юзера -> 400 Bad Request
    response = client.post(f"/api/photos/{photo.id}/rate", headers={"Authorization": voter_token}, json={"rate": 4})
    assert response.status_code == 400

    # 7. Отримання середнього рейтингу (Summary)
    response = client.get(f"/api/photos/{photo.id}/rate/summary", headers={"Authorization": voter_token})
    assert response.status_code == 200
    assert response.json()["average_rating"] == 5.0

    # Summary для неіснуючого фото -> 404
    response = client.get("/api/photos/999/rate/summary", headers={"Authorization": voter_token})
    assert response.status_code == 404

    # 8. Адмін успішно видаляє оцінку -> 204 No Content
    response = client.delete("/api/photos/rate/1", headers={"Authorization": admin_token})
    assert response.status_code == 204

    # Видалення неіснуючої оцінки -> 404
    response = client.delete("/api/photos/rate/999", headers={"Authorization": admin_token})
    assert response.status_code == 404
