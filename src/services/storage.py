import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException, status
from src.conf.config import settings

# NB:: configuring  cloudinary.config() ussually is performed
# in your configuration file (config.py) or main.py via environmental variables.
# If it has already been configured in other modules, there's no need to configure it again.

async def save_avatar_to_cloudinary(file: UploadFile, user_id: int) -> str:
    if settings.E2E_MODE:
        from src.services.e2e import save_fake_avatar
        return save_fake_avatar(file, user_id)
    try:
        # Upload to Cloudinary with avatar-specific optimization.
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
    if settings.E2E_MODE:
        from src.services.e2e import delete_fake_avatar
        delete_fake_avatar(user_id)
        return
    try:
        # Deleting the file by its public_id
        public_id = f"photoshare/avatars/user_{user_id}_avatar"
        cloudinary.uploader.destroy(public_id)
    except Exception:
        # If an error occurs during deletion, it can be ignored to avoid blocking the DB operation
        pass
