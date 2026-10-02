from pydantic import BaseModel, ConfigDict, Field

# Scheme for creating a rating
class RatingModel(BaseModel):
    rate: int = Field(..., ge=1, le=5, description="Rating of the photo from 1 to 5 stars")  # Rating of the photo from 1 to 5 stars

# Scheme for response (Response)
class RatingResponse(BaseModel):
    id: int
    photo_id: int
    user_id: int
    rate: int

    model_config = ConfigDict(from_attributes=True)

# Scheme for displaying the average rating of a photo
class PhotoRatingSummaryResponse(BaseModel):
    photo_id: int
    average_rating: float
    total_votes: int
