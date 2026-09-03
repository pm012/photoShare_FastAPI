from typing import Optional, List
from sqlalchemy.orm import Session
from src.database.models import Comment
from src.schemas.comments import CommentModel

def create_comment(photo_id: int, user_id: int, body: CommentModel, db: Session) -> Comment:
    new_comment = Comment(
        photo_id=photo_id,
        user_id=user_id,
        text=body.text
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment

def get_comment_by_id(comment_id: int, db: Session) -> Optional[Comment]:
    return db.query(Comment).filter(Comment.id == comment_id).first()

def get_comments_by_photo(photo_id: int, db: Session) -> List[Comment]:
    return db.query(Comment).filter(Comment.photo_id == photo_id).all()

def update_comment(comment_id: int, body: CommentModel, db: Session) -> Optional[Comment]:
    comment = get_comment_by_id(comment_id, db)
    if comment:
        comment.text = body.text
        db.commit()
        db.refresh(comment)
    return comment

def delete_comment(comment_id: int, db: Session) -> Optional[Comment]:
    comment = get_comment_by_id(comment_id, db)
    if comment:
        db.delete(comment)
        db.commit()
    return comment
