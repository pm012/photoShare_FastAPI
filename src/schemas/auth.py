from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from src.database.models import UserRole

# Схема для реєстрації нового користувача
class UserModel(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)

# Схема для повернення даних користувача (Response)
class UserDb(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime

    # Для сумісності з SQLAlchemy ORM моделями в Pydantic v2
    model_config = ConfigDict(from_attributes=True)

# Схема для JWT токена відповіді при логіні
class TokenModel(BaseModel):
    access_token: str
    token_type: str = "bearer"
