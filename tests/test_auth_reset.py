import jwt
from src.conf.config import settings
from datetime import datetime, timedelta, timezone

def test_request_password_reset(client):
    # Реєструємо користувача
    client.post("/api/auth/signup", json={"username": "reset_me", "email": "reset@test.com", "password": "oldpassword123"})
    
    # Запитуємо скидання пароля
    response = client.post("/api/auth/request_password_reset", json={"email": "reset@test.com"})
    assert response.status_code == 200
    assert response.json()["message"] == "If the email exists, a reset link has been sent."


def test_reset_password_with_valid_token(client):
    # Реєструємо користувача
    client.post("/api/auth/signup", json={"username": "reset_me", "email": "reset@test.com", "password": "oldpassword123"})

    # Вручну генеруємо валідний токен скидання, оскільки пошта замокана
    to_encode = {"sub": "reset@test.com", "exp": datetime.now(timezone.utc) + timedelta(hours=1), "scope": "password_reset"}
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    # Викликаємо ендпоінт скидання з новим паролем
    response = client.post(f"/api/auth/reset_password/{token}", json={"password": "newpassword123"})
    assert response.status_code == 200
    assert response.json()["message"] == "Password has been successfully updated. You can now log in."

    # Перевіряємо, що тепер можна успішно увійти під новим паролем
    login_response = client.post("/api/auth/login", data={"username": "reset@test.com", "password": "newpassword123"})
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()
