from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import User, UserRole
from src.schemas.ratings import RatingModel, RatingResponse, PhotoRatingSummaryResponse
from src.repository import ratings as repository_ratings
from src.repository import photos as repository_photos
from src.services.roles import RoleAccess

router = APIRouter(prefix="/photos", tags=["ratings"])

allowed_all = RoleAccess([UserRole.USER, UserRole.MODERATOR, UserRole.ADMIN])
# Видалення та перегляд усіх оцінок за ТЗ дозволено ТІЛЬКИ Moderator/Admin
allowed_management = RoleAccess([UserRole.MODERATOR, UserRole.ADMIN])

@router.post("/{photo_id}/rate", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
def rate_photo(
    photo_id: int,
    body: RatingModel,
    current_user: User = Depends(allowed_all),
    db: Session = Depends(get_db)
):
    # 1. Перевіряємо, чи існує світлина
    photo = repository_photos.get_photo_by_id(photo_id, db)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
        
    # 2. ТЗ: Неможливо оцінювати свої світлини
    if photo.user_id == current_user.id:
        raise HTTPException(            
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot rate your own photo."
        )
        
    # 3. Перевіряємо, чи цей користувач вже ставив оцінку (запобігаємо IntegrityError через UniqueConstraint)
    existing_ratings = repository_ratings.get_ratings_by_photo(photo_id, db)
    for r in existing_ratings:
        if r.user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already rated this photo. Only 1 rating per photo is allowed."
            )
            
    return repository_ratings.create_rate(photo_id, current_user.id, body.rate, db)


@router.get("/{photo_id}/rate/summary", response_model=PhotoRatingSummaryResponse)
def get_photo_rating_summary(photo_id: int, db: Session = Depends(get_db), current_user: User = Depends(allowed_all)):
    # Отримання середнього рейтингу світлини
    photo = repository_photos.get_photo_by_id(photo_id, db)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
        
    return repository_ratings.get_average_rating(photo_id, db)


@router.delete("/rate/{rating_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo_rating(
    rating_id: int,
    current_user: User = Depends(allowed_management), # ТІЛЬКИ Moderator/Admin за ТЗ
    db: Session = Depends(get_db)
):
    rating = repository_ratings.get_rating_by_id(rating_id, db)
    if not rating:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rating record not found")
        
    repository_ratings.delete_rate(rating_id, db)
    return None
