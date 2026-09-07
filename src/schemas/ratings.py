from pydantic import BaseModel, ConfigDict, Field

# Схема для створення оцінки
class RatingModel(BaseModel):
    rate: int = Field(..., ge=1, le=5, description="Оцінка світлини від 1 до 5 зірок")

# Схема відповіді (Response)
class RatingResponse(BaseModel):
    id: int
    photo_id: int
    user_id: int
    rate: int

    model_config = ConfigDict(from_attributes=True)

# Схема для виведення середнього рейтингу світлини
class PhotoRatingSummaryResponse(BaseModel):
    photo_id: int
    average_rating: float
    total_votes: int
