from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, field_validator

# Scheme for tag response
class TagResponse(BaseModel):
    id: int
    name: str
    
    model_config = ConfigDict(from_attributes=True)

# Scheme for photo response
class PhotoResponse(BaseModel):
    id: int
    user_id: int
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    url: str
    description: Optional[str] = None
    tags: List[TagResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Scheme for updating a photo: send the description, the tags, or both.
# A field that is not sent stays unchanged; "tags": [] removes all tags.
class PhotoUpdateDescription(BaseModel):
    description: Optional[str] = None
    tags: Optional[List[str]] = None

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, value):
        if value is None:
            return None
        cleaned = [tag.strip() for tag in value if tag and tag.strip()]
        if any(len(tag) > 30 for tag in cleaned):
            raise ValueError("Each tag must be at most 30 characters long.")
        return cleaned