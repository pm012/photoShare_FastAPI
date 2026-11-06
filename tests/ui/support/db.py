"""Direct access to the e2e database: seeding test data, verifying results, cleaning up.

Only ever constructed with a URL that passed config.assert_safe_database().
Rows are created through the application's own SQLAlchemy models, so schema changes are
picked up automatically. Deleting a user cascades (ORM) to their photos, comments, ratings.
"""
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime

import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

DEFAULT_PASSWORD = "Passw0rd!e2e"

# The backend settings object requires these at import time. Real values are irrelevant here
# because the test process never uses Cloudinary / SMTP.
_DUMMY_BACKEND_ENV = {
    "SECRET_KEY": "e2e_test_process_secret",
    "CLOUDINARY_NAME": "e2e", "CLOUDINARY_API_KEY": "e2e", "CLOUDINARY_API_SECRET": "e2e",
    "MAIL_USERNAME": "e2e@example.com", "MAIL_PASSWORD": "e2e", "MAIL_FROM": "e2e@example.com",
    "MAIL_SERVER": "smtp.example.com",
}


def _hash(password: str) -> str:
    # rounds=4 is the bcrypt minimum: fast tests; verification works with any cost factor.
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=4)).decode()


@dataclass(frozen=True)
class SeededUser:
    id: int
    username: str
    email: str
    password: str
    role: str


@dataclass(frozen=True)
class SeededPhoto:
    id: int
    owner_id: int
    description: str | None
    tags: tuple[str, ...]


class Database:
    def __init__(self, url: str, prefix: str):
        # Force every accidental use of the app's own session factory onto the e2e database
        # (and stop pydantic from reading the developer's .env file).
        os.environ["DATABASE_URL"] = url
        for key, value in _DUMMY_BACKEND_ENV.items():
            os.environ.setdefault(key, value)
        from src.database import models  # noqa: PLC0415  (must come after the env setup above)

        self.m = models
        self.prefix = prefix
        self.engine = create_engine(url, pool_pre_ping=True)

    def session(self) -> Session:
        return Session(self.engine, expire_on_commit=False)

    def sweep(self) -> None:
        """Delete everything this pytest session could have left behind (name prefix match)."""
        m = self.m
        with self.session() as s:
            for user in s.query(m.User).filter(m.User.username.startswith(self.prefix, autoescape=True)):
                s.delete(user)
            s.commit()
            for tag in s.query(m.Tag).filter(m.Tag.name.startswith(self.prefix, autoescape=True)):
                if not tag.photos:
                    s.delete(tag)
            s.commit()

    def dispose(self) -> None:
        self.engine.dispose()


@dataclass
class DataFactory:
    """Creates test data and removes it again. One instance per test (fixture `data`)."""
    db: Database
    namer: object
    base_url: str
    _user_ids: list[int] = field(default_factory=list)
    _usernames: list[str] = field(default_factory=list)
    _new_tags: set[str] = field(default_factory=set)

    # ------------------------------------------------------------------ create
    def user(self, role: str = "user", *, label: str | None = None, password: str = DEFAULT_PASSWORD,
             is_active: bool = True, avatar_url: str | None = None) -> SeededUser:
        m = self.db.m
        username = self.namer.username(label or role)
        email = self.namer.email(label or role)
        with self.db.session() as s:
            row = m.User(username=username, email=email, hashed_password=_hash(password), role=m.UserRole(role),
                         is_active=is_active, is_confirmed=True, avatar_url=avatar_url)
            s.add(row)
            s.commit()
            self._user_ids.append(row.id)
            return SeededUser(row.id, username, email, password, role)

    def photo(self, owner: SeededUser, *, description: str | None = None, tags: tuple[str, ...] = (),
              url: str | None = None, created_at: datetime | None = None) -> SeededPhoto:
        return self.photos(owner, 1, description=description, tags=tags, url=url, created_at=created_at)[0]

    def photos(self, owner: SeededUser, count: int, *, description: str | None = None,
               tags: tuple[str, ...] = (), url: str | None = None, created_at: datetime | None = None) -> list[SeededPhoto]:
        """`count` photos in one transaction (e.g. 21 for pagination tests). With count > 1 the
        description gets a running number suffix: "<description> #1", "#2", ..."""
        m = self.db.m
        # Default picture is the frontend's own favicon: no external service is involved.
        image_url = url or f"{self.base_url.rstrip('/')}/favicon.png"
        created: list[SeededPhoto] = []
        with self.db.session() as s:
            tag_rows = []
            for name in tags:
                tag = s.query(m.Tag).filter_by(name=name).first()
                if tag is None:
                    tag = m.Tag(name=name)
                    s.add(tag)
                    self._new_tags.add(name)
                tag_rows.append(tag)
            for index in range(1, count + 1):
                text = description if count == 1 or description is None else f"{description} #{index}"
                row = m.Photo(user_id=owner.id, url=image_url, public_id=f"e2e/{uuid.uuid4().hex}", description=text)
                if created_at is not None:
                    row.created_at = created_at
                row.tags = list(tag_rows)
                s.add(row)
                s.flush()
                created.append(SeededPhoto(row.id, owner.id, text, tuple(tags)))
            s.commit()
        return created

    def comment(self, photo: SeededPhoto, author: SeededUser, text: str) -> int:
        with self.db.session() as s:
            row = self.db.m.Comment(photo_id=photo.id, user_id=author.id, text=text)
            s.add(row)
            s.commit()
            return row.id

    def rating(self, photo: SeededPhoto, rater: SeededUser, rate: int) -> int:
        with self.db.session() as s:
            row = self.db.m.Rating(photo_id=photo.id, user_id=rater.id, rate=rate)
            s.add(row)
            s.commit()
            return row.id

    def update_user(self, user_id: int, **fields) -> None:
        """Change a seeded user directly in the DB, e.g. update_user(id, role="moderator", is_active=False)."""
        with self.db.session() as s:
            row = s.get(self.db.m.User, user_id)
            if "role" in fields:
                fields["role"] = self.db.m.UserRole(fields["role"])
            for key, value in fields.items():
                setattr(row, key, value)
            s.commit()

    def track_tag(self, name: str) -> None:
        """Register a tag that the UI created, so it is removed (if orphaned) afterwards."""
        self._new_tags.add(name)

    def track_username(self, username: str) -> None:
        """Register an account that the UI created (e.g. sign-up test) so it is deleted afterwards."""
        self._usernames.append(username)

    # ------------------------------------------------------------------ inspect
    def user_row(self, user_id: int | None = None, *, username: str | None = None) -> dict | None:
        m = self.db.m
        with self.db.session() as s:
            query = s.query(m.User)
            row = query.filter_by(id=user_id).first() if user_id is not None else query.filter_by(username=username).first()
            if row is None:
                return None
            return {"id": row.id, "username": row.username, "email": row.email, "role": row.role.value,
                    "is_active": row.is_active, "avatar_url": row.avatar_url}

    def photo_row(self, photo_id: int) -> dict | None:
        m = self.db.m
        with self.db.session() as s:
            row = s.get(m.Photo, photo_id)
            if row is None:
                return None
            return {"id": row.id, "description": row.description, "tags": sorted(t.name for t in row.tags)}

    def photos_of(self, user_id: int) -> list[dict]:
        m = self.db.m
        with self.db.session() as s:
            rows = s.query(m.Photo).filter_by(user_id=user_id).order_by(m.Photo.id).all()
            return [{"id": r.id, "description": r.description, "url": r.url, "tags": sorted(t.name for t in r.tags)} for r in rows]

    def comments_of(self, photo_id: int) -> list[str]:
        m = self.db.m
        with self.db.session() as s:
            return [c.text for c in s.query(m.Comment).filter_by(photo_id=photo_id).order_by(m.Comment.id)]

    def ratings_of(self, photo_id: int) -> list[int]:
        m = self.db.m
        with self.db.session() as s:
            return [r.rate for r in s.query(m.Rating).filter_by(photo_id=photo_id).order_by(m.Rating.id)]

    # ------------------------------------------------------------------ cleanup
    def cleanup(self) -> None:
        m = self.db.m
        with self.db.session() as s:
            for user_id in self._user_ids:
                row = s.get(m.User, user_id)
                if row is not None:
                    s.delete(row)
            for username in self._usernames:
                row = s.query(m.User).filter_by(username=username).first()
                if row is not None:
                    s.delete(row)
            s.commit()
            for name in self._new_tags:
                tag = s.query(m.Tag).filter_by(name=name).first()
                if tag is not None and not tag.photos:
                    s.delete(tag)
            s.commit()
        self._user_ids.clear()
        self._usernames.clear()
        self._new_tags.clear()
