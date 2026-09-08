from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import Request

from src.database.db import get_db
from src.database.models import User, UserRole
from src.schemas.users import UserPublicResponse, UserMeResponse, UserUpdateModel
from src.schemas.search import PhotoSearchResponse
from src.repository import users as repository_users
from src.repository import photos as repository_photos
from src.services.roles import RoleAccess
from src.services.limiter import limiter

router = APIRouter(prefix="/users", tags=["users"])

allowed_all = RoleAccess([UserRole.USER, UserRole.MODERATOR, UserRole.ADMIN])
allowed_admin = RoleAccess([UserRole.ADMIN])

@router.get("/me", response_model=UserMeResponse)
def get_current_user_profile(current_user: User = Depends(allowed_all)):
    # ТЗ: Власний профіль користувача
    return current_user


@router.put("/me", response_model=UserMeResponse)
@limiter.limit("10/minute")
def update_current_user_profile(
    request: Request,
    body: UserUpdateModel, 
    current_user: User = Depends(allowed_all), 
    db: Session = Depends(get_db)
):
    # ТЗ: Редагування власного профілю
    existing_user = repository_users.get_user_by_username(body.username, db)
    if existing_user and existing_user.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    try:
        return repository_users.update_user_me(current_user.id, body.username, db)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")


@router.get("/{username}", response_model=UserPublicResponse)
def get_user_public_profile(username: str, db: Session = Depends(get_db), current_user: User = Depends(allowed_all)):
    # ТЗ: Публічний профіль за унікальним юзернеймом
    profile_data = repository_users.get_user_profile_by_username(username, db)
    if not profile_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user, photos_count = profile_data
    return {"username": user.username, "created_at": user.created_at, "photos_count": photos_count}

@router.get("/{username}/photos", response_model=list[PhotoSearchResponse])
def get_user_public_photos(username: str, db: Session = Depends(get_db), current_user: User = Depends(allowed_all)):
    user = repository_users.get_user_by_username(username, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return repository_photos.search_photos(
        query_str=None,
        tag_name=None,
        sort_by="date",
        order="desc",
        db=db,
        user_id=user.id,
    )


@router.patch("/{user_id}/ban", response_model=UserMeResponse)
@limiter.limit("10/minute")
def ban_user(
    request: Request,
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

from src.schemas.users import UserRoleUpdateModel # <-- Додали імпорт нової схеми

@router.patch("/{user_id}/role", response_model=UserMeResponse)
@limiter.limit("10/minute")
def change_user_role(
    request: Request,
    user_id: int,
    body: UserRoleUpdateModel,
    current_user: User = Depends(allowed_admin),  # Тільки Admin може міняти ролі!
    db: Session = Depends(get_db)
):
    # Забороняємо адміну змінювати роль самому собі (щоб випадково не заблокувати доступ)
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="You cannot change your own role."
        )
        
    user = repository_users.change_user_role(user_id, body.role, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_user: User = Depends(allowed_all),  # Доступно всім авторизованим, але з логікою всередині
    db: Session = Depends(get_db)
):
    # 1. Захист: Адмін не може видалити самого себе
    if current_user.role == UserRole.ADMIN and current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="You cannot delete your own admin account."
        )

    # 2. Перевірка прав: видалити може або сам власник, або ADMIN
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this account."
        )

    user = repository_users.delete_user(user_id, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    return None
