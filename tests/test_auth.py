def test_signup_first_user_as_admin(client):
    # Тест ТЗ: Перший зареєстрований користувач стає admin
    response = client.post(
        "/api/auth/signup",
        json={
            "username": "admin_test",
            "email": "admin_test@example.com",
            "password": "supersecretpassword123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "admin_test"
    assert data["email"] == "admin_test@example.com"
    assert data["role"] == "admin"  # Перевірка логіки першого адміна
    assert data["is_active"] is True


def test_signup_second_user_as_user(client):
    # Другий користувач має автоматично отримати роль user
    response = client.post(
        "/api/auth/signup",
        json={
            "username": "regular_user",
            "email": "user_test@example.com",
            "password": "userpassword123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "user"  # Перевірка, що роль саме user


def test_login_success(client):
    # Перевіряємо успішний логін та видачу JWT токена
    response = client.post(
        "/api/auth/login",
        data={
            "username": "admin_test@example.com",  # OAuth2 форма очікує email в полі username
            "password": "supersecretpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client):
    # Перевірка обробки помилок при неправильному паролі
    response = client.post(
        "/api/auth/login",
        data={
            "username": "admin_test@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"
