# PhotoShare REST API

PhotoShare — це сучасний масштабований REST API застосунок (аналог Instagram, Photoshare, Pintrest), реалізований на фреймворку **FastAPI** з використанням архітектурного патерну **Repository/Service**. Проєкт підтримує рольову модель доступу (RBAC), завантаження медіафайлів у хмару Cloudinary, автоматичну генерацію QR-кодів, систему коментування та оцінок світлин, а також складний пошук із динамічною фільтрацією.

## Технологічний стек

- **Backend:** FastAPI, Python 3.14+
- **Управління залежностями:** Poetry 2.0+
- **База даних & ORM:** PostgreSQL, SQLAlchemy 2.0+
- **Міграції:** Alembic
- **Автентифікація:** JWT (PyJWT), нативний Bcrypt (passlib застарілий і для використання з новими версіями Python краще використовувати bcrypt)
- **Хмарне сховище:** Cloudinary SDK
- **Кешування & Чорний список токенів (Logout):** Redis
- **Захист від атак (Rate Limiting):** Slowapi (Redis storage)
- **Верифікація та пошта:** FastAPI-Mail (SMTP Ukr.net/Gmail)
- **Контейнеризація:** Docker, Docker Compose (Alpine-базовий образ)
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
   Створіть у корені файл `.env` та вкажіть ваші діючі ключі Cloudinary, пароль програми для SMTP пошти та інші налаштування:

   ```env
   DATABASE_URL=postgresql+psycopg2://postgres:secret_password@localhost:5433/photoshare_db
   SECRET_KEY=super_secret_key_change_me_in_production_1234567890
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   PUBLIC_API_URL=http://localhost:8000
   MAX_UPLOAD_SIZE_BYTES=10485760

   CLOUDINARY_NAME=your_cloudinary_name
   CLOUDINARY_API_KEY=your_cloudinary_api_key
   CLOUDINARY_API_SECRET=your_cloudinary_api_secret

   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_PASSWORD=replace_with_a_random_redis_password
   POSTGRES_PASSWORD=replace_with_a_random_database_password

   # Налаштування SMTP (приклади для Ukr.net)
   MAIL_USERNAME=your_login@ukr.net
   MAIL_PASSWORD=your_app_specific_password
   MAIL_FROM=your_login@ukr.net
   MAIL_PORT=465
   MAIL_SERVER=smtp.ukr.net

   # Режим розробки (False вимикає обов'язкове підтвердження пошти для тестів)
   MAIL_CONFIRMATION_REQUIRED=False
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

Для Docker Compose змінна `DATABASE_URL` всередині контейнера формується автоматично
через сервіс `db`; локальне значення в `.env` використовується лише для запуску поза Docker.

Проєкт буде доступний за адресою: **`http://localhost:8000`**  
Інтерактивна документація Swagger API: **`http://localhost:8000/docs`**

---

## Локальна розробка (без Docker для коду)

При потребі запускати та редагувати код локально у IDE за допомогою Poetry:

1. **Встановіть залежності проєкту:**

   ```bash
   poetry install
   ```

2. **Підніміть лише інфраструктуру (БД та Redis) в Docker:**

   ```bash
   docker compose up -d db redis
   ```

   _Увага!!! Якщо треба перестворити базу заново використовуйте замість цієї команди кілька наступних:_

   ```bash
   docker compose down -v
   docker compose up -d db redis
   ```

   Увага: docker compose down -v видаляє volumes, тому всі дані PostgreSQL буде втрачено.

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

Тести запускаються в повністю ізольованій базі даних у пам'яті (SQLite `:memory:`) та використовують моки для зовнішніх сервісів (Cloudinary, Redis, SMTP). Автоматичний лімітер запитів ізолюється на час тестів. Локальна база даних залишиться незмінною.

Виконайте команду у терміналі:

```bash
poetry run pytest -v
```

---

## Особливості Рольової Моделі (RBAC) & Захисту

- **User:** може завантажувати свої фото (макс. 3/хв), редагувати їхній опис, коментувати будь-які світлини, ставити їм оцінки від 1 до 5 зірок (крім власних), а також ініціювати видалення власного акаунта.
- **Moderator:** має всі права користувача + може видаляти/редагувати коментарі будь-кого та управляти оцінками. Не має доступу до адміністрування профілів.
- **Admin:** повний CRUD над усім контентом у системі + можливість блокування користувачів (`PATCH /api/users/{id}/ban`), динамічна зміна ролей для створення Модераторів/Адмінів (`PATCH /api/users/{id}/role`), а також примусове видалення шкідливих акаунтів.
- _Критичне правило з ТЗ:_ Перший зареєстрований користувач у базі даних (ID 1) автоматично отримує статус **Admin** та активований статус верифікації.

## Безпека та Інфраструктурні фічі

1. **Rate Limiting (Slowapi):** Ендпоінти створення контенту (фото, коментарі, оцінки, пошук) та авторизації захищені лімітами запитів через сесії Redis для протидії DDoS та брутфорсу.
2. **Email Верифікація:** Двоетапна реєстрація через токени підтвердження. Наявний повний цикл відновлення доступу (`/request_password_reset` та `/reset_password/{token}`).
3. **Docker Security:** Фінальний `Dockerfile` базується на захищеному Alpine образі, проводить повний апгрейд системних компонентів для закриття вразливостей High/Critical та використовує `.dockerignore` для мінімізації розміру контейнера.
