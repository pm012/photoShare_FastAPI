from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.database.db import get_db
from src.database.models import User, UserRole
from src.schemas.users import UserPublicResponse, UserMeResponse, UserUpdateModel, UserRoleUpdateModel
from src.schemas.search import PhotoSearchResponse
from src.repository import users as repository_users
from src.repository import photos as repository_photos
from src.services.roles import RoleAccess
from src.services.limiter import limiter
# Add import for Cloudinary service for saving avatars
from src.services.storage import save_avatar_to_cloudinary, delete_avatar_from_cloudinary

router = APIRouter(prefix="/users", tags=["users"])

allowed_all = RoleAccess([UserRole.USER, UserRole.MODERATOR, UserRole.ADMIN])
allowed_admin = RoleAccess([UserRole.ADMIN])

@router.get("/me", response_model=UserMeResponse)
def get_current_user_profile(current_user: User = Depends(allowed_all)):
    # PRD: Own profile of the user
    return current_user


@router.put("/me", response_model=UserMeResponse)
@limiter.limit("10/minute")
def update_current_user_profile(
    request: Request,
    body: UserUpdateModel, 
    current_user: User = Depends(allowed_all), 
    db: Session = Depends(get_db)
):
    # PRD: Editing own profile
    existing_user = repository_users.get_user_by_username(body.username, db)
    if existing_user and existing_user.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    try:
        return repository_users.update_user_me(current_user.id, body.username, db)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")


@router.post("/me/avatar", response_model=UserMeResponse)
@limiter.limit("5/minute")  # Protection against spam uploads
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(allowed_all),
    db: Session = Depends(get_db)
):
    # Cloud service Cloudinary automatically overwrites the old file due to public_id during a subsequent POST.
    # But if you want to be extra safe and forcibly delete the old public_id:
    # delete_avatar_from_cloudinary(current_user.id)

    # Upload the image to Cloudinary and get the HTTPS URL
    avatar_url = await save_avatar_to_cloudinary(file, current_user.id)
    
    # Update the avatar_url field in the database for the current user
    current_user.avatar_url = avatar_url
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/me/avatar", response_model=UserMeResponse)
def delete_avatar(
    current_user: User = Depends(allowed_all),
    db: Session = Depends(get_db)
):
    if not current_user.avatar_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User does not have an avatar.")
        
    # Delete the physical file from the Cloudinary
    delete_avatar_from_cloudinary(current_user.id)
    
    # Nullify the link in the database
    current_user.avatar_url = None
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/{username}", response_model=UserPublicResponse)
def get_user_public_profile(username: str, db: Session = Depends(get_db), current_user: User = Depends(allowed_all)):
    # PRD: Public profile by unique username
    profile_data = repository_users.get_user_profile_by_username(username, db)
    if not profile_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user, photos_count = profile_data
    # Updated: added transfer of avatar_url field to UserPublicResponse schema
    return {
        "username": user.username, 
        "created_at": user.created_at, 
        "photos_count": photos_count,
        "avatar_url": user.avatar_url
    }


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
    is_active: bool = False,  # False — ban, True — unban
    current_user: User = Depends(allowed_admin),  # Only Admin can ban users
    db: Session = Depends(get_db)
):
    # Disallow Admin from banning themselves
    if current_user.id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot ban yourself.")
        
    user = repository_users.ban_user(user_id, is_active, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/{user_id}/role", response_model=UserMeResponse)
@limiter.limit("10/minute")
def change_user_role(
    request: Request,
    user_id: int,
    body: UserRoleUpdateModel,
    current_user: User = Depends(allowed_admin),  # Only Admin can change roles!
    db: Session = Depends(get_db)
):
    # Disallow Admin from changing their own role (to prevent accidentally locking themselves out)
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
    current_user: User = Depends(allowed_all),  # Available to all authorized users, but with logic inside
    db: Session = Depends(get_db)
):
    # 1. Protection: Admin cannot delete themselves
    if current_user.role == UserRole.ADMIN and current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="You cannot delete your own admin account."
        )

    # 2. Permission check: can delete either the owner themselves or ADMIN
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this account."
        )

    # Before deleting the user from the database, also clear the cloud from their avatar
    delete_avatar_from_cloudinary(user_id)

    user = repository_users.delete_user(user_id, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    return None
