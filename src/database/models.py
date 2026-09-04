import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum, Table, UniqueConstraint
from sqlalchemy.orm import relationship
from src.database.db import Base

# Перелік ролей для RBAC (Role Based Access Control)
class UserRole(str, enum.Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"

# Таблиця зв'язку Many-to-Many між Фото та Тегами
photo_m2m_tag = Table(
    "photo_m2m_tag",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("photo_id", Integer, ForeignKey("photos.id", ondelete="CASCADE")),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE")),
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_confirmed = Column(Boolean, default=False, nullable=False)

    photos = relationship("Photo", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="user", cascade="all, delete-orphan")


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    url = Column(String(255), nullable=False)
    public_id = Column(String(100), nullable=False)  # Сховище Cloudinary public ID
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="photos")
    tags = relationship("Tag", secondary=photo_m2m_tag, back_populates="photos")
    comments = relationship("Comment", back_populates="photo", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="photo", cascade="all, delete-orphan")
    transformations = relationship("PhotoTransformation", back_populates="photo", cascade="all, delete-orphan")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(30), unique=True, nullable=False, index=True)

    photos = relationship("Photo", secondary=photo_m2m_tag, back_populates="tags")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    photo_id = Column(Integer, ForeignKey("photos.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    photo = relationship("Photo", back_populates="comments")
    user = relationship("User", back_populates="comments")


class PhotoTransformation(Base):
    __tablename__ = "photo_transformations"

    id = Column(Integer, primary_key=True, index=True)
    photo_id = Column(Integer, ForeignKey("photos.id", ondelete="CASCADE"), nullable=False)
    transformed_url = Column(String(255), nullable=False)
    qr_code_url = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    photo = relationship("Photo", back_populates="transformations")


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    photo_id = Column(Integer, ForeignKey("photos.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rate = Column(Integer, nullable=False)

    photo = relationship("Photo", back_populates="ratings")
    user = relationship("User", back_populates="ratings")

    # Складений унікальний індекс: один користувач може поставити лише 1 оцінку конкретній світлині
    __table_args__ = (
        UniqueConstraint('photo_id', 'user_id', name='_photo_user_uc'),
    )
