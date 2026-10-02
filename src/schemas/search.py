from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from src.schemas.photos import TagResponse

# Scheme for returning a photo with its average rating in the search results
class PhotoSearchResponse(BaseModel):
    id: int
    user_id: int
    username: str
    url: str
    description: Optional[str] = None
    tags: List[TagResponse] = []
    created_at: datetime
    average_rating: float  # For visualization when filtering by rating (average - with a floating point)
    model_config = ConfigDict(from_attributes=True)
