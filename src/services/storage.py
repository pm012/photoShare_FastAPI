import cloudinary
import cloudinary.uploader
from pathlib import Path
from fastapi import UploadFile, HTTPException, status

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 3 * 1024 * 1024  # 3 MB

# NB:: configuring  cloudinary.config() ussually is performed
# in your configuration file (config.py) or main.py via environmental variables.
# If it has already been configured in other modules, there's no need to configure it again.

async def save_avatar_to_cloudinary(file: UploadFile, user_id: int) -> str:
    # 1. Validation of extension and MIME type
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Allowed only the following formats: JPEG, PNG, WEBP."
        )

    # 2. Validation of file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must not exceed 3MB."
        )
    
    # Return the file pointer to the beginning for further reading
    await file.seek(0)

    try:
        # 3. Loading to Cloudinary with the optimization (Best Practice for avatars)
        response = cloudinary.uploader.upload(
            file.file,
            public_id=f"user_{user_id}_avatar",  # A unique ID for the user (replaces the old one on re-upload)
            folder="photoshare/avatars",       # A separate folder in Cloudinary
            overwrite=True,
            transformation=[
                {"width": 250, "height": 250, "crop": "fill", "gravity": "face"}, # Automatically centers on the face and makes a 250x250 square
                {"quality": "auto"},
                {"fetch_format": "auto"}
            ]
        )
        # Return the direct HTTPS link to the optimized image
        return response.get("secure_url")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading image to cloud: {str(e)}"
        )

def delete_avatar_from_cloudinary(user_id: int) -> None:
    try:
        # Deleting the file by its public_id
        public_id = f"photoshare/avatars/user_{user_id}_avatar"
        cloudinary.uploader.destroy(public_id)
    except Exception:
        # If an error occurs during deletion, it can be ignored to avoid blocking the DB operation
        pass
