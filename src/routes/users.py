from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import User, UserRole
from src.schemas.users import UserPublicResponse, UserMeResponse, UserUpdateModel
from src.repository import users as repository_users
from src.services.auth import auth_service
from src.services.roles import RoleAccess

router = APIRouter(prefix="/users", tags=["users"])

allowed_all = RoleAccess([UserRole.USER, UserRole.MODERATOR, UserRole.ADMIN])
allowed_admin = RoleAccess([UserRole.ADMIN])

@router.get("/me", response_model=UserMeResponse)
def get_current_user_profile(current_user: User = Depends(allowed_all)):
    # ТЗ: Власний профіль користувача
    return current_user


@router.put("/me", response_model=UserMeResponse)
def update_current_user_profile(
    body: UserUpdateModel, 
    current_user: User = Depends(allowed_all), 
    db: Session = Depends(get_db)
):
    # ТЗ: Редагування власного профілю
    return repository_users.update_user_me(current_user.id, body.username, db)


@router.get("/{username}", response_model=UserPublicResponse)
def get_user_public_profile(username: str, db: Session = Depends(get_db), current_user: User = Depends(allowed_all)):
    # ТЗ: Публічний профіль за унікальним юзернеймом
    profile_data = repository_users.get_user_profile_by_username(username, db)
    if not profile_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user, photos_count = profile_data
    return {"username": user.username, "created_at": user.created_at, "photos_count": photos_count}


@router.patch("/{user_id}/ban", response_model=UserMeResponse)
def ban_user(
    user_id: int, 
    is_active: bool = False,  # False — забанити, True — розбанити
    current_user: User = Depends(allowed_admin),  # ТІЛЬКИ Admin за ТЗ
    db: Session = Depends(get_db)
):
    # Забороняємо адміну банити самого себе
    if current_user.id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot ban yourself.")
        
    user = repository_users.ban_user(user_id, is_active, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
