from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

# Схема тегу для відповіді
class TagResponse(BaseModel):
    id: int
    name: str
    
    model_config = ConfigDict(from_attributes=True)

# Схема відповіді на успішне завантаження/отримання фото
class PhotoResponse(BaseModel):
    id: int
    user_id: int
    url: str
    description: Optional[str] = None
    tags: List[TagResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Схема для оновлення опису фото
class PhotoUpdateDescription(BaseModel):
    description: str
