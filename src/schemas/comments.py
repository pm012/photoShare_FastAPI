from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

#   Scheme for creating or editing a comment
class CommentModel(BaseModel):
    text: str = Field(min_length=1, max_length=500)

# Scheme for server response (Response)
class CommentResponse(BaseModel):
    id: int
    photo_id: int
    user_id: int
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    text: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)