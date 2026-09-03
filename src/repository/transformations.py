from sqlalchemy.orm import Session
from src.database.models import PhotoTransformation

def create_transformation(photo_id: int, transformed_url: str, qr_code_url: str, db: Session) -> PhotoTransformation:
    new_transform = PhotoTransformation(
        photo_id=photo_id,
        transformed_url=transformed_url,
        qr_code_url=qr_code_url
    )
    db.add(new_transform)
    db.commit()
    db.refresh(new_transform)
    return new_transform
