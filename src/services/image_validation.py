from io import BytesIO

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

# Pillow format name -> content types that are accepted for it
ALLOWED_IMAGE_TYPES = {
    "JPEG": {"image/jpeg", "image/jpg"},
    "PNG": {"image/png"},
    "WEBP": {"image/webp"},
}
ALLOWED_CONTENT_TYPES = {content_type for types in ALLOWED_IMAGE_TYPES.values() for content_type in types}


async def validate_image_upload(file: UploadFile, max_bytes: int) -> None:
    """Reject files that are not real JPEG/PNG/WEBP images or are larger than max_bytes.

    The file position is reset afterwards, so the file can be uploaded to Cloudinary as usual.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPEG, PNG, and WEBP are supported.",
        )

    # Read at most one byte more than allowed: enough to know the file is too large.
    data = await file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Image exceeds the maximum allowed size of {max_bytes // (1024 * 1024)} MB.",
        )

    try:
        with Image.open(BytesIO(data)) as image:
            image.verify()
            if image.format not in ALLOWED_IMAGE_TYPES or file.content_type not in ALLOWED_IMAGE_TYPES[image.format]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File content does not match its declared image type.",
                )
    except (UnidentifiedImageError, OSError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not a valid image.",
        )
    finally:
        await file.seek(0)
