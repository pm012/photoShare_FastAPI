from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

# Scheme for tag response
class TagResponse(BaseModel):
    id: int
    name: str
    
    model_config = ConfigDict(from_attributes=True)

# Scheme for photo response
class PhotoResponse(BaseModel):
    id: int
    user_id: int
    url: str
    description: Optional[str] = None
    tags: List[TagResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Scheme for updating photo description
class PhotoUpdateDescription(BaseModel):
    description: str
