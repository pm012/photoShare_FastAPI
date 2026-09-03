from datetime import datetime
from pydantic import BaseModel, ConfigDict

# Схема для вхідних даних (вибір пресету трансформації)
class TransformationCreate(BaseModel):
    # Очікуємо один з варіантів: "avatar", "black_white", "thumbnail"
    preset: str 

# Схема для повернення результату користувачу (Response)
class TransformationResponse(BaseModel):
    id: int
    photo_id: int
    transformed_url: str
    qr_code_url: str
    created_at: datetime

    # Вмикаємо сумісність з SQLAlchemy ORM моделями для Pydantic v2
    model_config = ConfigDict(from_attributes=True)
