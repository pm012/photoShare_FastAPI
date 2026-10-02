from typing import List, Optional
from sqlalchemy import func, desc, asc
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.database.models import Rating, Photo, Tag, User, photo_m2m_tag
from src.schemas.photos import PhotoUpdateDescription

def process_tags(tags_list: List[str], db: Session) -> List[Tag]:
    # BRD: Limit up to 5 tags per photo
    if len(tags_list) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can add a maximum of 5 tags to a photo."
        )
    
    db_tags = []
    for tag_name in tags_list:
        tag_name = tag_name.strip().lower()
        if not tag_name:
            continue
        # Searching if there is such global tag
        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            # Creating new tag if there is no tag
            tag = Tag(name=tag_name)
            db.add(tag)
            db.commit()
            db.refresh(tag)
        db_tags.append(tag)
    return db_tags

def create_photo(user_id: int, url: str, public_id: str, description: Optional[str], tags_list: List[str], db: Session) -> Photo:
    # Handle tags using unique logic
    tags = process_tags(tags_list, db)
    
    new_photo = Photo(
        user_id=user_id,
        url=url,
        public_id=public_id,
        description=description,
        tags=tags
    )
    db.add(new_photo)
    db.commit()
    db.refresh(new_photo)
    return new_photo

def get_photo_by_id(photo_id: int, db: Session) -> Optional[Photo]:
    return db.query(Photo).filter(Photo.id == photo_id).first()

def update_photo_description(photo_id: int, body: PhotoUpdateDescription, current_user: User, db: Session) -> Optional[Photo]:
    photo = get_photo_by_id(photo_id, db)
    if not photo:
        return None
    
    # BRD: Update description can only owner or Admin
    if photo.user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit this photo description."
        )
        
    photo.description = body.description
    db.commit()
    db.refresh(photo)
    return photo

def delete_photo(photo_id: int, current_user: User, db: Session) -> Optional[Photo]:
    photo = get_photo_by_id(photo_id, db)
    if not photo:
        return None
        
    # BRD: Delete photo can only owner or Admin
    if photo.user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this photo."
        )
        
    db.delete(photo)
    db.commit()
    return photo

def search_photos(
    query_str: Optional[str],
    tag_name: Optional[str],
    sort_by: str,
    order: str,
    db: Session,
    user_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    min_rating: Optional[float] = None,
) -> List[dict]:
    # Basic request and calculation of the average mark
    search_query = db.query(
        Photo,
        func.coalesce(func.avg(Rating.rate), 0.0).label("avg_rating")
    ).outerjoin(Rating, Photo.id == Rating.photo_id)

    # Filter by description
    if query_str:
        search_query = search_query.filter(Photo.description.ilike(f"%{query_str}%"))

    # Filter by tag
    if tag_name:
        tag_name = tag_name.strip().lower()
        search_query = search_query.join(Photo.tags).filter(Tag.name == tag_name)
    if user_id is not None:
        search_query = search_query.filter(Photo.user_id == user_id)

    # Group for correct aggregation
    search_query = search_query.group_by(Photo.id)
    if min_rating is not None:
        search_query = search_query.having(func.coalesce(func.avg(Rating.rate), 0.0) >= min_rating)

    # Define field for sorting (per BRD)
    sort_field = "avg_rating" if sort_by == "rating" else Photo.created_at

    # Sorting direction is applied dynamically (ASC / DESC)
    if order == "asc":
        search_query = search_query.order_by(asc(sort_field))
    else:
        search_query = search_query.order_by(desc(sort_field))

    results = search_query.offset((page - 1) * page_size).limit(page_size).all()

    mapped_results = []
    for photo, avg_rating in results:
        mapped_results.append({
            "id": photo.id,
            "user_id": photo.user_id,
            "username": photo.user.username,
            "url": photo.url,
            "description": photo.description,
            "tags": photo.tags,
            "created_at": photo.created_at,
            "average_rating": round(avg_rating, 2)
        })
    return mapped_results
