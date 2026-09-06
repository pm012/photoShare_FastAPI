import jwt
from src.conf.config import settings
from src.routes import auth as auth_route
from datetime import datetime, timedelta, timezone

def test_request_password_reset(client):
    # Реєструємо користувача
    client.post("/api/auth/signup", json={"username": "reset_me", "email": "reset@test.com", "password": "oldpassword123"})
    
    # Запитуємо скидання пароля
    response = client.post("/api/auth/request_password_reset", json={"email": "reset@test.com"})
    assert response.status_code == 200
    assert response.json()["message"] == "If the email exists, a reset link has been sent."


def test_password_reset_email_uses_configured_public_url(client, monkeypatch):
    captured = {}

    async def capture_reset_email(email, username, host):
        captured["host"] = host

    monkeypatch.setattr(auth_route, "send_reset_password_email", capture_reset_email)
    monkeypatch.setattr(settings, "PUBLIC_API_URL", "https://photoshare.example")
    client.post(
        "/api/auth/signup",
        json={"username": "public_url", "email": "public-url@test.com", "password": "password123"},
    )
    response = client.post(
        "/api/auth/request_password_reset",
        headers={"Host": "attacker.example"},
        json={"email": "public-url@test.com"},
    )

    assert response.status_code == 200
    assert captured["host"] == "https://photoshare.example/"


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


def test_reset_password_token_is_one_time(client, monkeypatch):
    client.post(
        "/api/auth/signup",
        json={"username": "one_time", "email": "one-time@test.com", "password": "oldpassword123"},
    )
    used_tokens = set()
    monkeypatch.setattr(
        "src.routes.auth.blacklist_service.is_token_blacklisted",
        lambda token: token in used_tokens,
    )
    monkeypatch.setattr(
        "src.routes.auth.blacklist_service.add_to_blacklist",
        lambda token, ttl: used_tokens.add(token),
    )
    token = jwt.encode(
        {
            "sub": "one-time@test.com",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "scope": "password_reset",
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    assert client.post(
        f"/api/auth/reset_password/{token}",
        json={"password": "newpassword123"},
    ).status_code == 200
    replay = client.post(
        f"/api/auth/reset_password/{token}",
        json={"password": "anotherpassword123"},
    )
    assert replay.status_code == 400
