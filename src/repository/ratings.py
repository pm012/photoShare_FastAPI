from typing import Optional, List
from sqlalchemy import func
from sqlalchemy.orm import Session
from src.database.models import Rating, Photo

def create_rate(photo_id: int, user_id: int, rate: int, db: Session) -> Rating:
    new_rating = Rating(
        photo_id=photo_id,
        user_id=user_id,
        rate=rate
    )
    db.add(new_rating)
    db.commit()
    db.refresh(new_rating)
    return new_rating

def get_rating_by_id(rating_id: int, db: Session) -> Optional[Rating]:
    return db.query(Rating).filter(Rating.id == rating_id).first()

def get_ratings_by_photo(photo_id: int, db: Session) -> List[Rating]:
    return db.query(Rating).filter(Rating.photo_id == photo_id).all()

# Обчислення середньої оцінки за ТЗ
def get_average_rating(photo_id: int, db: Session) -> dict:
    # Робимо запит, який рахує середнє (avg) та кількість (count)
    result = db.query(
        func.avg(Rating.rate).label("average"),
        func.count(Rating.id).label("total")
    ).filter(Rating.photo_id == photo_id).first()
    
    # Якщо оцінок немає, повертаємо 0.0
    avg_rate = round(result.average, 2) if result.average else 0.0
    total_votes = result.total if result.total else 0
    
    return {
        "photo_id": photo_id,
        "average_rating": avg_rate,
        "total_votes": total_votes
    }

def delete_rate(rating_id: int, db: Session) -> Optional[Rating]:
    rating = get_rating_by_id(rating_id, db)
    if rating:
        db.delete(rating)
        db.commit()
    return rating
