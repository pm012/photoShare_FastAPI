import io
import qrcode
from src.services.cloudinary import cloudinary_service

def generate_qr_code_url(target_url: str, username: str, photo_id: int) -> str:
    # 1. Генерируємо QR-код в пам'яті (BytesIO)
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(target_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # Створюємо буфер у пам'яті
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    # 2. Огортаємо буфер у структуру, яку зрозуміє наш Cloudinaryuploader
    class FakeFile:
        def __init__(self, file_bytes):
            self.file = file_bytes

    fake_upload_file = FakeFile(img_byte_arr)

    # 3. Завантажуємо QR-код в Cloudinary в окрему папку користувача
    cloudinary_result = cloudinary_service.upload_photo(
        fake_upload_file, 
        f"{username}/qrcodes_photo_{photo_id}"
    )
    return cloudinary_result.get("secure_url")
