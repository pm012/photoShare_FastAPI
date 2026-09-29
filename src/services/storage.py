import cloudinary
import cloudinary.uploader
from pathlib import Path
from fastapi import UploadFile, HTTPException, status

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 3 * 1024 * 1024  # 3 MB

# Зверніть увагу: налаштування cloudinary.config() зазвичай виконується 
# у вашому файлі конфігурації (config.py) або main.py через змінні оточення.
# Якщо воно вже працює в інших модулях, тут конфігурувати наново не потрібно.

async def save_avatar_to_cloudinary(file: UploadFile, user_id: int) -> str:
    # 1. Валідація розширення та MIME-типу
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Дозволені лише зображення форматів: JPEG, PNG, WEBP."
        )

    # 2. Валідація розміру файлу
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Розмір файлу не повинен перевищувати 3MB."
        )
    
    # Повертаємо покажчик на початок файлу для подальшого читання
    await file.seek(0)

    try:
        # 3. Завантаження у Cloudinary з оптимізацією (Best Practice для аватарів)
        response = cloudinary.uploader.upload(
            file.file,
            public_id=f"user_{user_id}_avatar",  # Один унікальний ID для користувача (перезаписує старий при повторному завантаженні)
            folder="photoshare/avatars",       # Окрема папка в Cloudinary
            overwrite=True,
            transformation=[
                {"width": 250, "height": 250, "crop": "fill", "gravity": "face"}, # Автоматично центрує на обличчі та робить квадрат 250х250
                {"quality": "auto"},
                {"fetch_format": "auto"}
            ]
        )
        # Повертаємо пряме HTTPS посилання на оптимізоване зображення
        return response.get("secure_url")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка завантаження зображення у хмару: {str(e)}"
        )

def delete_avatar_from_cloudinary(user_id: int) -> None:
    try:
        # Видаляємо файл за його public_id
        public_id = f"photoshare/avatars/user_{user_id}_avatar"
        cloudinary.uploader.destroy(public_id)
    except Exception:
        # При видаленні помилку можна проігнорувати, щоб не блокувати роботу БД
        pass
