from threading import Lock

from sqlalchemy import text
from sqlalchemy.orm import Session
from src.database.models import User, UserRole
from src.schemas.auth import UserModel
from src.services.auth import auth_service
from src.conf.config import settings  

_user_creation_lock = Lock()

# Перевірка, чи є користувач першим у базі
def is_first_user(db: Session) -> bool:
    return db.query(User).count() == 0

# Отримання користувача за email
def get_user_by_email(email: str, db: Session) -> User:
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(username: str, db: Session) -> User:
    return db.query(User).filter(User.username == username).first()

# Створення нового користувача в БД з урахуванням логіки першого Admin та Dev-режиму
def create_user(body: UserModel, db: Session) -> User:
    with _user_creation_lock:
        if db.bind.dialect.name == "postgresql":
            db.execute(text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": 735_120_401})

        is_first = is_first_user(db)
        role = UserRole.ADMIN if is_first else UserRole.USER

        # Перший admin або dev-режим не потребує email confirmation.
        auto_confirm = is_first or not settings.MAIL_CONFIRMATION_REQUIRED

        hashed_password = auth_service.get_password_hash(body.password)
        new_user = User(
            username=body.username,
            email=body.email,
            hashed_password=hashed_password,
            role=role,
            is_active=True,
            is_confirmed=auto_confirm,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
