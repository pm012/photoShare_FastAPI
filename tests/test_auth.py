def test_signup_first_user_as_admin(client):
    # Тест: Перший зареєстрований — admin
    response = client.post(
        "/api/auth/signup",
        json={
            "username": "admin_test",
            "email": "admin_test@example.com",
            "password": "supersecretpassword123"
        }
    )
    assert response.status_code == 201
    assert response.json()["role"] == "admin"


def test_signup_second_user_as_user(client):
    # Спочатку створюємо першого (він забере роль admin)
    client.post(
        "/api/auth/signup",
        json={"username": "first_admin", "email": "admin@test.com", "password": "password123"}
    )
    
    # Тепер створюємо другого — він зобов'язаний стати user
    response = client.post(
        "/api/auth/signup",
        json={
            "username": "regular_user",
            "email": "user_test@example.com",
            "password": "userpassword123"
        }
    )
    assert response.status_code == 201
    assert response.json()["role"] == "user"  # Тепер цей assert пройде на 100%


def test_login_success(client):
    # Оскільки БД порожня, спочатку реєструємо акаунт для входу
    client.post(
        "/api/auth/signup",
        json={
            "username": "admin_test",
            "email": "admin_test@example.com",
            "password": "supersecretpassword123"
        }
    )
    
    # Тепер логінимося в нього
    response = client.post(
        "/api/auth/login",
        data={
            "username": "admin_test@example.com",
            "password": "supersecretpassword123"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_invalid_credentials(client):
    response = client.post(
        "/api/auth/login",
        data={
            "username": "nobody@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
