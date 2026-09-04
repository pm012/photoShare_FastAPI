from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr
from src.database.models import UserRole

# Публічний профіль користувача (доступний усім)
class UserPublicResponse(BaseModel):
    username: str
    created_at: datetime
    photos_count: int  # ТЗ: Кількість завантажених фото

    model_config = ConfigDict(from_attributes=True)

# Детальний власний профіль
class UserMeResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Схема для редагування власного профілю
class UserUpdateModel(BaseModel):
    username: str

# Схема для редагування ролі не адміна адміном
class UserRoleUpdateModel(BaseModel):
    role: UserRole
