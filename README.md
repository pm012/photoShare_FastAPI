# PhotoShare REST API 📸

PhotoShare — це сучасний масштабований REST API застосунок (аналог Instagram), реалізований на фреймворку **FastAPI** з використанням архітектурного патерну **Repository/Service**. Проєкт підтримує рольову модель доступу (RBAC), завантаження медіафайлів у хмару Cloudinary, автоматичну генерацію QR-кодів, систему коментування та оцінок світлин, а також складний пошук із динамічною фільтрацією.

## 🛠 Технологічний стек

- **Backend:** FastAPI, Python 3.14+
- **Управління залежностями:** Poetry 2.0+
- **База даних & ORM:** PostgreSQL, SQLAlchemy 2.0+
- **Міграції:** Alembic
- **Автентифікація:** JWT (PyJWT), нативний Bcrypt
- **Хмарне сховище:** Cloudinary SDK
- **Кешування & Чорний список токенів (Logout):** Redis
- **Контейнеризація:** Docker, Docker Compose
- **Тестування:** Pytest (ізольована SQLite в пам'яті)

---

## Швидкий запуск через Docker Compose (В один клік)

Найпростіший спосіб підняти весь проєкт локально разом із базою даних та Redis:

1. **Клонуйте репозиторій:**

   ```bash
   git clone https://github.com/pm012/photoShare_FastAPI.git
   cd photoShare_FastAPI
   ```

2. **Налаштуйте змінні оточення:**
   Створіть у корені файл `.env` та вкажіть ваші діючі ключі Cloudinary (можна безкоштовно отримати на cloudinary.com):

   ```env
   DATABASE_URL=postgresql+psycopg2://postgres:secret_password@localhost:5433/photoshare_db
   SECRET_KEY=super_secret_key_change_me_in_production_1234567890
   CLOUDINARY_NAME=your_cloudinary_name
   CLOUDINARY_API_KEY=your_cloudinary_api_key
   CLOUDINARY_API_SECRET=your_cloudinary_api_secret
   REDIS_HOST=localhost
   REDIS_PORT=6379
   ```

3. **Запустіть контейнери:**

   ```bash
   docker compose up --build
   ```

4. **Застосуйте міграції Alembic всередині контейнера:**
   Відкрийте нове вікно терміналу та виконайте:
   ```bash
   docker compose exec web poetry run alembic upgrade head
   ```

Проєкт буде доступний за адресою: **`http://localhost:8000`**  
Інтерактивна документація Swagger API: **`http://localhost:8000/docs`**

---

## Локальна розробка (без Docker для коду)

Якщо ви хочете запускати та редагувати код локально у вашій IDE за допомогою Poetry:

1. **Встановіть залежності проєкту:**

   ```bash
   poetry install
   ```

2. **Підніміть лише інфраструктуру (БД та Redis) в Docker:**

   ```bash
   docker compose up -d db redis
   ```

3. **Застосуйте міграції до локальної БД:**

   ```bash
   poetry run alembic upgrade head
   ```

4. **Запустіть сервер розробки Uvicorn:**
   ```bash
   poetry run python main.py
   ```

---

## Запуск автоматичних тестів (Pytest)

Усі тести запускаються в повністю ізольованій базі даних у пам'яті (SQLite `:memory:`) та використовують моки для зовнішніх сервісів (Cloudinary, Redis). Ваша локальна база даних залишиться неушкодженою.

Виконайте команду у терміналі:

```bash
poetry run pytest -v
```

---

## Особливості Рольової Моделі (RBAC)

- **User:** може завантажувати свої фото, редагувати їхній опис, коментувати будь-які світлини та ставити їм оцінки (крім власних).
- **Moderator:** має всі права користувача + може видаляти/редагувати коментарі будь-кого та управляти оцінками.
- **Admin:** повний CRUD над усім контентом у системі + можливість банити користувачів (`PATCH /api/users/{id}/ban`).
- _💡 Критичне правило з ТЗ:_ Перший зареєстрований користувач у базі даних (ID 1) автоматично отримує статус **Admin**.
