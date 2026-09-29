from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from src.database.models import User, Photo, UserRole

def get_user_profile_by_username(username: str, db: Session) -> Optional[Tuple[User, int]]:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    # Рахуємо кількість фото користувача
    photos_count = db.query(Photo).filter(Photo.user_id == user.id).count()
    return user, photos_count

def get_user_by_username(username: str, db: Session) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

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

def search_users_admin(search_str: str, db: Session, page: int = 1, page_size: int = 20) -> List[User]:
    # Шукаємо користувачів за частковим збігом в username або email (ігноруючи регістр)
    users_query = db.query(User)
    if search_str:
        users_query = users_query.filter(
            (User.username.ilike(f"%{search_str}%")) |
            (User.email.ilike(f"%{search_str}%"))
        )
    return users_query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
def delete_user(user_id: int, db: Session) -> Optional[User]:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
    return user



def change_user_role(user_id: int, new_role: UserRole, db: Session) -> Optional[User]:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.role = new_role
        db.commit()
        db.refresh(user)
    return user