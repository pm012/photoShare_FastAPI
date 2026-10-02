import cloudinary
import cloudinary.uploader
from fastapi import UploadFile
from src.conf.config import settings

class CloudinaryService:
    def __init__(self):
        # Initialisation of Cloudinary from the .env file via settings
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True
        )

    def upload_photo(self, file: UploadFile, username: str) -> dict:
        # Uploading photo to the user's original folder
        folder_path = f"PhotoShare/{username}"
        result = cloudinary.uploader.upload(
            file.file, 
            folder=folder_path,
            overwrite=True,
            resource_type="image"
        )
        return result

    def delete_photo(self, public_id: str) -> dict:
        # Deleting photo from the cloud by its public_id
        result = cloudinary.uploader.destroy(public_id)
        return result

    def get_transformed_url(self, public_id: str, preset: str) -> str:
        # Sets of transformations according to the requirements
        transformation_options = []
        
        if preset == "avatar":
            transformation_options = [{"width": 400, "height": 400, "crop": "fill", "gravity": "face", "radius": "max"}]
        elif preset == "black_white":
            transformation_options = [{"effect": "blackwhite"}]
        elif preset == "thumbnail":
            transformation_options = [{"width": 250, "height": 250, "crop": "thumb"}]
        else:
            transformation_options = [{"width": 800, "crop": "scale"}]

        # Generating URL with the array of transformations
        url = cloudinary.CloudinaryImage(public_id).build_url(transformation=transformation_options)
        return url

cloudinary_service = CloudinaryService()
