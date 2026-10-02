import jwt
from src.database.models import User
from src.conf.config import settings

def test_signup_first_user_as_admin(client):
    # Test: The first who registered - admin
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
    # At first create the first (he will obtain admin role)
    client.post(
        "/api/auth/signup",
        json={"username": "first_admin", "email": "admin@test.com", "password": "password123"}
    )
    
    # Now signup second -  he should become user
    response = client.post(
        "/api/auth/signup",
        json={
            "username": "regular_user",
            "email": "user_test@example.com",
            "password": "userpassword123"
        }
    )
    assert response.status_code == 201
    assert response.json()["role"] == "user"  


def test_login_success(client):
    # As BD is empty, register account to enter at first
    client.post(
        "/api/auth/signup",
        json={
            "username": "admin_test",
            "email": "admin_test@example.com",
            "password": "supersecretpassword123"
        }
    )
    
    # Login to the created above account
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


def test_login_requires_email_confirmation(client, db_session, monkeypatch):
    settings.MAIL_CONFIRMATION_REQUIRED = True
    user = User(
        username="unconfirmed",
        email="unconfirmed@example.com",
        hashed_password="",
        is_confirmed=False,
    )
    from src.services.auth import auth_service
    user.hashed_password = auth_service.get_password_hash("password123")
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/auth/login",
        data={"username": user.email, "password": "password123"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Email address is not confirmed"

def test_confirm_email_invalid_token(client):
    response = client.get("/api/auth/confirmed/invalid_token_here")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired verification token"

def test_confirm_email_already_confirmed(client):
    # Create user
    client.post("/api/auth/signup", json={"username": "confirmed_user", "email": "conf@test.com", "password": "password"})
    
    # Generateing token 
    to_encode = {"sub": "conf@test.com", "scope": "email_verification"}
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    response = client.get(f"/api/auth/confirmed/{token}")
    assert response.status_code == 200
    assert response.json()["message"] == "Your email is already confirmed."


def test_reset_password_invalid_scope(client):
    # Token has incorrect scope
    to_encode = {"sub": "admin@test.com", "scope": "wrong_scope"}
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    response = client.post(f"/api/auth/reset_password/{token}", json={"password": "newpassword"})
    assert response.status_code == 400
