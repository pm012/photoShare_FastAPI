from sqlalchemy.orm import Session
from src.database.models import User, UserRole
from src.schemas.auth import UserModel
from src.services.auth import auth_service

# Перевірка, чи є користувач першим у базі
def is_first_user(db: Session) -> bool:
    return db.query(User).count() == 0

# Отримання користувача за email
def get_user_by_email(email: str, db: Session) -> User:
    return db.query(User).filter(User.email == email).first()

# Створення нового користувача в БД з урахуванням логіки першого Admin
def create_user(body: UserModel, db: Session) -> User:
    # Визначаємо роль: якщо користувачів у системі ще немає, він стає ADMIN
    role = UserRole.ADMIN if is_first_user(db) else UserRole.USER
    
    hashed_password = auth_service.get_password_hash(body.password)
    
    new_user = User(
        username=body.username,
        email=body.email,
        hashed_password=hashed_password,
        role=role,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
