from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import User, UserRole
from src.schemas.comments import CommentModel, CommentResponse
from src.repository import comments as repository_comments
from src.repository import photos as repository_photos
from src.services.roles import RoleAccess

router = APIRouter(prefix="/photos", tags=["comments"])

# Дозволяємо базові операції всім ролям
allowed_all = RoleAccess([UserRole.USER, UserRole.MODERATOR, UserRole.ADMIN])
# Видалення коментарів за ТЗ дозволено ТІЛЬКИ Модераторам та Адмінам
allowed_delete = RoleAccess([UserRole.MODERATOR, UserRole.ADMIN])

@router.post("/{photo_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    photo_id: int,
    body: CommentModel,
    current_user: User = Depends(allowed_all),
    db: Session = Depends(get_db)
):
    # Перевіряємо, чи існує світлина, яку хочемо прокоментувати
    photo = repository_photos.get_photo_by_id(photo_id, db)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
        
    return repository_comments.create_comment(photo_id, current_user.id, body, db)


@router.get("/{photo_id}/comments", response_model=List[CommentResponse])
def get_comments(photo_id: int, db: Session = Depends(get_db), current_user: User = Depends(allowed_all)):
    photo = repository_photos.get_photo_by_id(photo_id, db)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
        
    return repository_comments.get_comments_by_photo(photo_id, db)


@router.put("/comments/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: int,
    body: CommentModel,
    current_user: User = Depends(allowed_all),
    db: Session = Depends(get_db)
):
    comment = repository_comments.get_comment_by_id(comment_id, db)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        
    # ТЗ: Користувач може редагувати свій коментар, а Адмін чи Модератор — будь-який
    if comment.user_id != current_user.id and current_user.role not in [UserRole.MODERATOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own comments."
        )
        
    return repository_comments.update_comment(comment_id, body, db)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    current_user: User = Depends(allowed_delete),  # Сюди потраплять тільки Moderator/Admin
    db: Session = Depends(get_db)
):
    comment = repository_comments.get_comment_by_id(comment_id, db)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        
    repository_comments.delete_comment(comment_id, db)
    return None
