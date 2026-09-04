import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from src.database.db import get_db, Base
from src.services.blacklist import blacklist_service
from src.services.limiter import limiter  # Імпортуємо лімітер
from src.services import email as service_email  # Імпортуємо сервіс імейлів

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session, monkeypatch):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    # 🔥 1. ВИМИКАЄМО RATE LIMITER ДЛЯ ТЕСТІВ, щоб не було помилок 429
    limiter.enabled = False

    # 🔥 2. МОКАЄМО ВІДПРАВКУ ЛИСТІВ (Заглушка, яка нічого не відправляє і не гальмує тести)
    async def mock_send_email(email, username, host):
        return None
    monkeypatch.setattr(service_email, "send_verification_email", mock_send_email)

    # Мокаємо сервіс чорного списку Redis
    monkeypatch.setattr(blacklist_service, "is_token_blacklisted", lambda token: False)
    monkeypatch.setattr(blacklist_service, "add_to_blacklist", lambda token, ttl: None)

    with TestClient(app) as test_client:
        yield test_client
        
    app.dependency_overrides.clear()
