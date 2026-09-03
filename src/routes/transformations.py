from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import User, UserRole
from src.schemas.transformations import TransformationCreate, TransformationResponse
from src.repository import photos as repository_photos
from src.repository import transformations as repository_transformations
from src.services.cloudinary import cloudinary_service
from src.services.qrcode import generate_qr_code_url
from src.services.roles import RoleAccess

router = APIRouter(prefix="/photos", tags=["transformations"])

allowed_all = RoleAccess([UserRole.USER, UserRole.MODERATOR, UserRole.ADMIN])

@router.post("/{photo_id}/transform", response_model=TransformationResponse, status_code=status.HTTP_201_CREATED)
def transform_photo(
    photo_id: int,
    body: TransformationCreate,
    current_user: User = Depends(allowed_all),
    db: Session = Depends(get_db)
):
    # 1. Перевіряємо, чи існує оригінальне фото
    photo = repository_photos.get_photo_by_id(photo_id, db)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")

    # Перевіряємо пресети за ТЗ ("avatar", "black_white", "thumbnail")
    if body.preset not in ["avatar", "black_white", "thumbnail"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid preset name")

    # 2. Генеруємо трансформований URL через Cloudinary
    transformed_url = cloudinary_service.get_transformed_url(photo.public_id, body.preset)

    # 3. Генеруємо QR-код, який веде на цей URL, та заливаємо його на Cloudinary
    try:
        qr_code_url = generate_qr_code_url(transformed_url, current_user.username, photo.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"QR-code generation error: {str(e)}"
        )

    # 4. Записуємо трансформацію в БД
    transformation = repository_transformations.create_transformation(
        photo_id=photo.id,
        transformed_url=transformed_url,
        qr_code_url=qr_code_url,
        db=db
    )
    return transformation
