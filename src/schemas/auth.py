from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from src.database.models import UserRole

# Scheme for registering a new user
class UserModel(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)

# Scheme for returning user data (Response)
class UserDb(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime

    # For compatibility with SQLAlchemy ORM models in Pydantic v2
    model_config = ConfigDict(from_attributes=True)

# Scheme for JWT token response during login
class TokenModel(BaseModel):
    access_token: str
    token_type: str = "bearer"
    
class RequestEmail(BaseModel):
    email: EmailStr

class ResetPasswordModel(BaseModel):
    password: str = Field(min_length=6, max_length=100)

