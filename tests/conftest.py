import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from main import app
from src.database.db import get_db, Base
from src.services.blacklist import blacklist_service

# 1. Налаштовуємо ізольовану БД в пам'яті для тестів
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 2. Фікстура для створення таблиць та керування сесією БД
@pytest.fixture(scope="package", autouse=True)
def setup_database():
    # Перед тестами створюємо всі таблиці ORM моделей
    Base.metadata.create_all(bind=engine)
    yield
    # Після завершення всіх тестів пакету — видаляємо таблиці
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# 3. Фікстура для клієнта тестування FastAPI (TestClient)
@pytest.fixture(scope="function")
def client(db_session, monkeypatch):
    # Перевизначаємо залежність get_db, щоб роути дивилися в тестову БД
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    # Заглушка (Mock) для Redis blacklist_service, щоб тести не вимагали запущеного Redis
    monkeypatch.setattr(blacklist_service, "is_token_blacklisted", lambda token: False)
    monkeypatch.setattr(blacklist_service, "add_to_blacklist", lambda token, ttl: None)

    with TestClient(app) as test_client:
        yield test_client
        
    # Очищуємо перевизначення після тесту
    app.dependency_overrides.clear()
