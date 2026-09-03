from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

# Схема для створення або редагування коментаря
class CommentModel(BaseModel):
    text: str = Field(min_length=1, max_length=500)

# Схема для відповіді сервера (Response)
class CommentResponse(BaseModel):
    id: int
    photo_id: int
    user_id: int
    text: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
