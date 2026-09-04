from sqlalchemy.orm import Session
from src.database.models import User, UserRole
from src.schemas.auth import UserModel
from src.services.auth import auth_service
from src.conf.config import settings  

# Перевірка, чи є користувач першим у базі
def is_first_user(db: Session) -> bool:
    return db.query(User).count() == 0

# Отримання користувача за email
def get_user_by_email(email: str, db: Session) -> User:
    return db.query(User).filter(User.email == email).first()

# Створення нового користувача в БД з урахуванням логіки першого Admin та Dev-режиму
def create_user(body: UserModel, db: Session) -> User:
    is_first = is_first_user(db)
    role = UserRole.ADMIN if is_first else UserRole.USER
    
    # Якщо це перший юзер (Адмін) АБО якщо верифікацію поштою вимкнено в .env -> підтверджуємо одразу
    auto_confirm = True if (is_first or not settings.MAIL_CONFIRMATION_REQUIRED) else False
    
    hashed_password = auth_service.get_password_hash(body.password)
    
    new_user = User(
        username=body.username,
        email=body.email,
        hashed_password=hashed_password,
        role=role,
        is_active=True,
        is_confirmed=auto_confirm  # <-- 🔥 2. ЗАСТОСУВАЛИ ЗМІННУ ЗАМІСТЬ ХАРДКОДУ
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
