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
    keyword: Optional[str] = Query(None, description="Keyword for searching in photo descriptions"),
    tag: Optional[str] = Query(None, description="Tag name for searching"),
    sort_by: str = Query("date", enum=["date", "rating"], description="Sorting field: by date or rating"),
    order: str = Query("desc", enum=["asc", "desc"], description="Sorting direction: asc (ascending) or desc (descending)"), # Parameter for sorting method (asc or desc)
    user_id: Optional[int] = Query(None, description="Author ID; available to moderators and administrators"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of photos per page"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum average rating for filtering photos"),
    current_user: User = Depends(allowed_all),
    db: Session = Depends(get_db)
):
    if user_id is not None and current_user.role not in [UserRole.MODERATOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only moderators and administrators can filter by user.",
        )
    # Pass the new order parameter to the repository
    return repository_photos.search_photos(
        query_str=keyword, 
        tag_name=tag, 
        sort_by=sort_by, 
        order=order, 
        db=db,
        user_id=user_id,
        page=page,
        page_size=page_size,
        min_rating=min_rating,
    )

@router.get("/users", response_model=List[UserMeResponse])
def search_users_for_admin(
    query: Optional[str] = Query(None, min_length=1, description="Name or Email of the user"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of users per page"),
    current_user: User = Depends(allowed_management),  # PRD requirement: only  Moderator/Admin can see other users
    db: Session = Depends(get_db)
):
    # Admin search for users by PRD requirements
    return repository_users.search_users_admin(
        search_str=query or "",
        db=db,
        page=page,
        page_size=page_size,
    )
