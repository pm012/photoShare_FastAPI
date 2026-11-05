"""Helpers that exist ONLY for UI tests. Imported when settings.E2E_MODE is true.

* FakeCloudinaryService / save_fake_avatar: store images in a local folder instead of Cloudinary.
* install_e2e_routes: serves that folder at /e2e-media and exposes /e2e/info so the test suite
  can verify it is talking to an e2e-mode backend that uses the expected database.
"""
import os
import tempfile
import uuid
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, UploadFile
from fastapi.staticfiles import StaticFiles
from PIL import Image

from src.conf.config import settings

MEDIA_URL_PATH = "/e2e-media"
MEDIA_DIR = Path(os.environ.get("E2E_MEDIA_DIR") or Path(tempfile.gettempdir()) / "photoshare-e2e-media")
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


def _media_url(file_name: str) -> str:
    return f"{settings.PUBLIC_API_URL.rstrip('/')}{MEDIA_URL_PATH}/{file_name}"


def _store(file: UploadFile, prefix: str) -> str:
    """Write the uploaded image to MEDIA_DIR and return the stored file name."""
    data = file.file.read()
    try:
        extension = (Image.open(BytesIO(data)).format or "png").lower()
    except Exception:
        extension = "png"
    file_name = f"{prefix}{uuid.uuid4().hex}.{extension}"
    (MEDIA_DIR / file_name).write_bytes(data)
    return file_name


class FakeCloudinaryService:
    """Same interface as src.services.cloudinary.CloudinaryService."""

    def upload_photo(self, file: UploadFile, username: str) -> dict:
        file_name = _store(file, prefix="photo_")
        return {"secure_url": _media_url(file_name), "public_id": f"e2e/{file_name}"}

    def delete_photo(self, public_id: str) -> dict:
        (MEDIA_DIR / public_id.removeprefix("e2e/")).unlink(missing_ok=True)
        return {"result": "ok"}

    def get_transformed_url(self, public_id: str, preset: str) -> str:
        # Same image; the query string only makes the "transformed" URL distinguishable.
        return f"{_media_url(public_id.removeprefix('e2e/'))}?preset={preset}"


def save_fake_avatar(file: UploadFile, user_id: int) -> str:
    delete_fake_avatar(user_id)
    return _media_url(_store(file, prefix=f"avatar_{user_id}_"))


def delete_fake_avatar(user_id: int) -> None:
    for path in MEDIA_DIR.glob(f"avatar_{user_id}_*"):
        path.unlink(missing_ok=True)


def install_e2e_routes(app: FastAPI) -> None:
    app.mount(MEDIA_URL_PATH, StaticFiles(directory=MEDIA_DIR), name="e2e-media")

    @app.get("/e2e/info", tags=["e2e"])
    def e2e_info():
        return {"e2e": True, "database": urlsplit(settings.DATABASE_URL).path.lstrip("/")}
