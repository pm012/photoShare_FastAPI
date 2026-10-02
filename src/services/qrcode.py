import io
import qrcode
from src.services.cloudinary import cloudinary_service

def generate_qr_code_url(target_url: str, username: str, photo_id: int) -> str:
    # 1. Generate QR code in memory (BytesIO)
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(target_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # Create buffer in memory
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    # 2. Wrap the buffer in a structure that our Cloudinary uploader can understand
    class FakeFile:
        def __init__(self, file_bytes):
            self.file = file_bytes

    fake_upload_file = FakeFile(img_byte_arr)

    # 3. Upload the QR code to Cloudinary in a separate folder for the user
    cloudinary_result = cloudinary_service.upload_photo(
        fake_upload_file, 
        f"{username}/qrcodes_photo_{photo_id}"
    )
    return cloudinary_result.get("secure_url")
