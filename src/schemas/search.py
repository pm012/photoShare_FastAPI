from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from src.schemas.photos import TagResponse

# Схема для повернення світлини з її середнім рейтингом у результатах пошуку
class PhotoSearchResponse(BaseModel):
    id: int
    user_id: int
    username: str
    url: str
    description: Optional[str] = None
    tags: List[TagResponse] = []
    created_at: datetime
    average_rating: float  # Для наочності при фільтрації за рейтингом (середнє - з плаваючою точкою)

    model_config = ConfigDict(from_attributes=True)
