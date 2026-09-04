from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi import Request
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import User, UserRole
from src.schemas.photos import PhotoResponse, PhotoUpdateDescription
from src.repository import photos as repository_photos
from src.services.auth import auth_service
from src.services.cloudinary import cloudinary_service
from src.services.roles import RoleAccess
from src.services.limiter import limiter

router = APIRouter(prefix="/photos", tags=["photos"])

# Права доступу: завантажувати, читати, редагувати та видаляти можуть усі авторизовані користувачі,
# але всередині репозиторію стоїть блок — едіт/видалення тільки для власника або Admin.
allowed_all = RoleAccess([UserRole.USER, UserRole.MODERATOR, UserRole.ADMIN])

@router.post("/", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def upload_photo(
    request: Request,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # Передаємо списком через кому за ТЗ (наприклад: "nature, sunset, sea")
    current_user: User = Depends(allowed_all),
    db: Session = Depends(get_db)
):
    # Валідація типу файлу (захист від завантаження шкідливих скриптів)
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg", "image/webp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid file type. Only JPEG, JPG, PNG, and WEBP are supported."
        )

    # 1. Завантажуємо файл у Cloudinary
    try:
        cloudinary_result = cloudinary_service.upload_photo(file, current_user.username)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cloudinary upload error: {str(e)}"
        )

    # 2. Парсимо теги з рядка, розділеного комами
    tags_list = []
    if tags:
        tags_list = [t.strip() for t in tags.split(",") if t.strip()]

    # 3. Зберігаємо посилання та метадані у базу даних
    photo = repository_photos.create_photo(
        user_id=current_user.id,
        url=cloudinary_result.get("secure_url"),
        public_id=cloudinary_result.get("public_id"),
        description=description,
        tags_list=tags_list,
        db=db
    )
    return photo


@router.get("/{photo_id}", response_model=PhotoResponse)
def get_photo(photo_id: int, db: Session = Depends(get_db), current_user: User = Depends(allowed_all)):
    photo = repository_photos.get_photo_by_id(photo_id, db)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return photo


@router.put("/{photo_id}", response_model=PhotoResponse)
@limiter.limit("5/minute")
def update_photo_description(
    request: Request,
    photo_id: int, 
    body: PhotoUpdateDescription, 
    current_user: User = Depends(allowed_all), 
    db: Session = Depends(get_db)
):
    photo = repository_photos.update_photo_description(photo_id, body, current_user, db)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return photo


@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo(photo_id: int, current_user: User = Depends(allowed_all), db: Session = Depends(get_db)):
    # Спочатку дізнаємося public_id з бази, щоб видалити файл і з хмари також
    photo = repository_photos.get_photo_by_id(photo_id, db)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    
    # Видаляємо з бази (всередині стоїть перевірка прав власник/адмін)
    repository_photos.delete_photo(photo_id, current_user, db)
    
    # Видаляємо фізичний файл з Cloudinary хмари
    cloudinary_service.delete_photo(photo.public_id)
    return None
