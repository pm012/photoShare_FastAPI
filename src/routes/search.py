from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi import Request
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import User, UserRole
from src.schemas.search import PhotoSearchResponse
from src.schemas.users import UserMeResponse
from src.repository import photos as repository_photos
from src.repository import users as repository_users
from src.services.roles import RoleAccess
from src.services.limiter import limiter

router = APIRouter(prefix="/search", tags=["search"])

allowed_all = RoleAccess([UserRole.USER, UserRole.MODERATOR, UserRole.ADMIN])
allowed_management = RoleAccess([UserRole.MODERATOR, UserRole.ADMIN])

@router.get("/photos", response_model=List[PhotoSearchResponse])
@limiter.limit("15/minute")
def search_photos(
    request: Request,
    keyword: Optional[str] = Query(None, description="Ключове слово для пошуку в описі світлини"),
    tag: Optional[str] = Query(None, description="Назва тегу для пошуку"),
    sort_by: str = Query("date", enum=["date", "rating"], description="Поле сортування: за датою або рейтингом"),
    order: str = Query("desc", enum=["asc", "desc"], description="Напрямок сортування: asc (за зростанням) або desc (за спаданням)"), # <-- НАШ НОВИЙ ПАРАМЕТР
    current_user: User = Depends(allowed_all),
    db: Session = Depends(get_db)
):
    # Передаємо новий параметр order у репозиторій
    return repository_photos.search_photos(
        query_str=keyword, 
        tag_name=tag, 
        sort_by=sort_by, 
        order=order, 
        db=db
    )

@router.get("/users", response_model=List[UserMeResponse])
def search_users_for_admin(
    query: str = Query(..., min_length=1, description="Ім'я або Email користувача"),
    current_user: User = Depends(allowed_management),  # ТІЛЬКИ Moderator/Admin за ТЗ
    db: Session = Depends(get_db)
):
    # Адмінський пошук користувачів за ТЗ
    return repository_users.search_users_admin(search_str=query, db=db)
