import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from src.database.db import get_db, Base
from src.services.blacklist import blacklist_service

# 1. Тестова БД в пам'яті
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 2.Фікстура сесії: очищує та створює таблиці на кожен тест індивідуально
@pytest.fixture(scope="function")
def db_session():
    # Перед КОЖНИМ тестом створюємо таблиці з нуля
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Після КОЖНОГО тесту повністю видаляємо структуру, гарантуючи ізоляцію
        Base.metadata.drop_all(bind=engine)


# 3. Фікстура клієнта тестування
@pytest.fixture(scope="function")
def client(db_session, monkeypatch):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    # Мокаємо сервіс чорного списку токенів Redis
    monkeypatch.setattr(blacklist_service, "is_token_blacklisted", lambda token: False)
    monkeypatch.setattr(blacklist_service, "add_to_blacklist", lambda token, ttl: None)

    with TestClient(app) as test_client:
        yield test_client
        
    app.dependency_overrides.clear()
