from datetime import datetime
from pydantic import BaseModel, ConfigDict

# Scheme for input data (selecting a transformation preset)
class TransformationCreate(BaseModel):
    # We expect one of the following options: "avatar", "black_white", "thumbnail"
    preset: str 

# Scheme for returning the result to the user (Response)
class TransformationResponse(BaseModel):
    id: int
    photo_id: int
    transformed_url: str
    qr_code_url: str
    created_at: datetime

    # Enabling compatibility with SQLAlchemy ORM models for Pydantic v2
    model_config = ConfigDict(from_attributes=True)
