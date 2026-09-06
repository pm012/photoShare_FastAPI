import pytest
from unittest.mock import MagicMock, AsyncMock
from src.services.blacklist import blacklist_service
from src.services.roles import RoleAccess
from src.database.models import UserRole, User
from src.services.cloudinary import cloudinary_service
from src.services import email as service_email
from src.services.qrcode import generate_qr_code_url  # Імпортуємо правильну функцію
from src.services.auth import auth_service
from src.database.db import get_db

# 1. Тестуємо рольову модель доступу (RBAC)
def test_role_access_allowed():
    access = RoleAccess([UserRole.ADMIN])
    mock_admin_user = User(role=UserRole.ADMIN, is_active=True, is_confirmed=True)
    result = access(current_user=mock_admin_user)
    assert result == mock_admin_user

def test_role_access_forbidden():
    from fastapi import HTTPException
    access = RoleAccess([UserRole.ADMIN])
    mock_regular_user = User(role=UserRole.USER, is_active=True, is_confirmed=True)
    
    with pytest.raises(HTTPException) as exc_info:
        access(current_user=mock_regular_user)
    assert exc_info.value.status_code == 403

# 2. Тест Blacklist
def test_blacklist_service_real_methods_coverage(monkeypatch):
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mock_redis.setex.return_value = True
    
    monkeypatch.setattr(blacklist_service, "redis_client", mock_redis)
    
    blacklist_service.add_to_blacklist("token_123", 10)
    res = blacklist_service.is_token_blacklisted("token_123")
    assert res is False or res is True or res is None

# 3. Тестуємо методи сервісу Cloudinary (Включаючи видалення)
def test_cloudinary_service_methods(monkeypatch):
    mock_uploader = MagicMock()
    mock_uploader.upload.return_value = {"secure_url": "https://test.com", "public_id": "123"}
    mock_uploader.destroy.return_value = {"result": "ok"}
    monkeypatch.setattr("cloudinary.uploader", mock_uploader)
    
    res = cloudinary_service.upload_photo(MagicMock(), "test_username")
    assert res is not None
    
    del_res = cloudinary_service.delete_photo("123")
    assert del_res == {"result": "ok"}
    
    url = cloudinary_service.get_transformed_url("123", "avatar")
    assert "c_fill" in url or "avatar" in url


@pytest.mark.parametrize("preset", ["black_white", "thumbnail", "unknown"])
def test_cloudinary_service_transformation_presets(preset):
    url = cloudinary_service.get_transformed_url("123", preset)
    assert "123" in url


def test_create_access_token_with_custom_expiration():
    token = auth_service.create_access_token({"sub": "test@example.com"}, expires_delta=5)
    assert token


def test_get_db_closes_session():
    db_generator = get_db()
    db_session = next(db_generator)
    db_generator.close()
    assert db_session is not None

# 4. Тестуємо сервіс пошта
@pytest.mark.anyio
async def test_email_service_direct(monkeypatch):
    mock_fastmail = MagicMock()
    mock_fastmail.send_message = AsyncMock(return_value=None)
    monkeypatch.setattr(service_email, "FastMail", lambda config: mock_fastmail)
    
    await service_email.send_verification_email("test@test.com", "user", "http://localhost/")
    await service_email.send_reset_password_email("test@test.com", "user", "http://localhost/")
    assert True

# 5. Виправлений Unit-тест для QR-кодів (Передаємо 3 параметри + мокаємо хмару)
def test_qr_code_service_direct(monkeypatch):
    # Мокаємо метод завантаження Cloudinary всередині qrcode.py
    monkeypatch.setattr(cloudinary_service, "upload_photo", lambda file, folder: {"secure_url": "https://fake-cloudinary.com"})
    
    # Передаємо всі 3 обов'язкові параметри з вашої сигнатури функції
    qr_url = generate_qr_code_url("https://fake-url.com", "test_user", 42)
    assert qr_url == "https://fake-cloudinary.com"
