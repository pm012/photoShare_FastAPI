from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from src.database.models import User, Photo

def get_user_profile_by_username(username: str, db: Session) -> Optional[Tuple[User, int]]:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    # Рахуємо кількість фото користувача
    photos_count = db.query(Photo).filter(Photo.user_id == user.id).count()
    return user, photos_count

def update_user_me(user_id: int, username: str, db: Session) -> Optional[User]:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.username = username
        db.commit()
        db.refresh(user)
    return user

def ban_user(user_id: int, ban_status: bool, db: Session) -> Optional[User]:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_active = ban_status
        db.commit()
        db.refresh(user)
    return user

def search_users_admin(search_str: str, db: Session) -> List[User]:
    # Шукаємо користувачів за частковим збігом в username або email (ігноруючи регістр)
    return db.query(User).filter(
        (User.username.ilike(f"%{search_str}%")) | 
        (User.email.ilike(f"%{search_str}%"))
    ).all()