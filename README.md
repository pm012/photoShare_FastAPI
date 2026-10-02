# PhotoShare REST API

PhotoShare is a modern, scalable REST API application inspired by photo-sharing platforms. It is built with **FastAPI** and follows the **Repository/Service** architectural pattern. The project supports role-based access control (RBAC), cloud media uploads to Cloudinary, automatic QR code generation, photo comments and ratings, and advanced search with dynamic filtering.

## Technology Stack

- **Backend:** FastAPI, Python 3.14+
- **Dependency management:** Poetry 2.0+
- **Database and ORM:** PostgreSQL, SQLAlchemy 2.0+
- **Migrations:** Alembic
- **Authentication:** JWT (PyJWT), native Bcrypt (passlib is deprecated; bcrypt is recommended for newer Python versions)
- **Cloud storage:** Cloudinary SDK
- **Caching and token blacklist (logout):** Redis
- **Rate limiting:** Slowapi (Redis storage)
- **Email verification:** FastAPI-Mail (SMTP via Ukr.net/Gmail)
- **Containerization:** Docker, Docker Compose (Alpine-based image)
- **Testing:** Pytest (isolated in-memory SQLite)

---

## Quick Start with Docker Compose

Compose starts the complete local stack: PostgreSQL, Redis, the FastAPI API, and the built React frontend.

1. **Clone the repository:**

   ```bash
   git clone https://github.com/pm012/photoShare_FastAPI.git
   cd photoShare_FastAPI
   ```

2. **Configure environment variables:**
   Create a root `.env` file based on `env-sample.cfg`. Add valid Cloudinary credentials, an SMTP app password, and any other required settings:

   ```env
   DATABASE_URL=postgresql+psycopg2://postgres:secret_password@localhost:5433/photoshare_db
   SECRET_KEY=super_secret_key_change_me_in_production_1234567890
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   PUBLIC_API_URL=http://localhost:8000
   FRONTEND_URL=http://localhost:5173
   VITE_API_URL=http://localhost:8000/api
   MAX_UPLOAD_SIZE_BYTES=10485760

   CLOUDINARY_NAME=your_cloudinary_name
   CLOUDINARY_API_KEY=your_cloudinary_api_key
   CLOUDINARY_API_SECRET=your_cloudinary_api_secret

   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_PASSWORD=replace_with_a_random_redis_password
   POSTGRES_PASSWORD=replace_with_a_random_database_password

   # SMTP settings (Ukr.net examples)
   MAIL_USERNAME=your_login@ukr.net
   MAIL_PASSWORD=your_app_specific_password
   MAIL_FROM=your_login@ukr.net
   MAIL_PORT=465
   MAIL_SERVER=smtp.ukr.net

   # Development mode (False disables mandatory email confirmation for tests)
   MAIL_CONFIRMATION_REQUIRED=False
   ```

3. **Start the containers:**

   ```bash
   docker compose up --build
   ```

4. **Run Alembic migrations inside the container:**
   Open another terminal and run:

   ```bash
   docker compose exec web poetry run alembic upgrade head
   ```

Inside the Docker Compose container, `DATABASE_URL` is configured automatically through the `db` service. The local value in `.env` is only used when running outside Docker.

The application is available at **`http://localhost:5173`**.
The API is available at **`http://localhost:8000`**.
Interactive Swagger API documentation is available at **`http://localhost:8000/docs`**.

To rebuild after frontend or backend changes, run `docker compose up --build`. To completely remove the local database, run `docker compose down -v`.

---

## Local Development (Run the Code Outside Docker)

To run and edit the code locally in an IDE with Poetry:

1. **Install project dependencies:**

   ```bash
   poetry install
   ```

2. **Start only the infrastructure (database and Redis) in Docker:**

   ```bash
   docker compose up -d db redis
   ```

   To recreate the database, run these commands instead:

   ```bash
   docker compose down -v
   docker compose up -d db redis
   ```

   Warning: `docker compose down -v` removes volumes, so all PostgreSQL data will be lost.

3. **Apply migrations to the local database:**

   ```bash
   poetry run alembic upgrade head
   ```

4. **Start the Uvicorn development server:**

   ```bash
   poetry run python main.py
   ```

5. **Start the frontend in development mode:**

   ```bash
   cd frontend
   npm ci
   npm run dev
   ```

   By default, the frontend connects to `http://localhost:8000/api`. To use a different address, copy `frontend/frontend-env-sample.cfg` to `frontend/.env` and update the value:

   ```env
   VITE_API_URL=https://your-api.example.com/api
   ```

   Vite automatically loads `frontend/.env`, and variables prefixed with `VITE_` are available in the code through `import.meta.env`. Do not store passwords, tokens, or private keys in this file: frontend variables are bundled into JavaScript and exposed to browser users.

---

## Deployment to Render

The recommended Render configuration consists of two services:

1. **Backend Web Service**
   - Repository: this repository
   - Environment: `Docker`
   - Dockerfile Path: `./Dockerfile`
   - Docker Context: repository root
   - Health Check Path: `/health`
   - Pre-Deploy Command: `alembic upgrade head`

   Render provides the port through the `PORT` environment variable; the root `Dockerfile` uses it automatically.

2. **Frontend Static Site**
   - Root Directory: `frontend`
   - Build Command: `npm ci && npm run build`
   - Publish Directory: `dist`
   - Rewrite Rule: `/*` -> `/index.html` with the `Rewrite` status

   Add a `VITE_API_URL` environment variable to the frontend Static Site with the value `https://<backend-service>.onrender.com/api`. The `frontend/frontend-env-sample.cfg` file is only a template for local development.

Add the environment variables from `env-sample.cfg` to the Backend Web Service. Production values must include:

- `DATABASE_URL` — the Internal Database URL from Render PostgreSQL;
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` — Redis service settings;
- `PUBLIC_API_URL` — the public backend URL;
- `FRONTEND_URL` — the public frontend Static Site URL. Multiple origins can be separated by commas;
- `SECRET_KEY`, Cloudinary, and SMTP variables — real production secrets;
- `MAIL_CONFIRMATION_REQUIRED=True`.

After creating both services, update `FRONTEND_URL` with the actual Static Site URL. Do not commit `.env` files or production secrets to the repository.

---

## Running Automated Tests (Pytest)

Tests run against a fully isolated in-memory SQLite database (`:memory:`) and mock external services (Cloudinary, Redis, SMTP). The rate limiter is disabled during tests, so the local database remains unchanged.

Run the following command in a terminal:

```bash
poetry run pytest -v
```

---

## Role-Based Access Control (RBAC) and Security

- **User:** can upload photos (up to 3 per minute), edit their descriptions, comment on any photo, rate photos from 1 to 5 stars (except their own), and request deletion of their account.
- **Moderator:** has all user permissions, can delete or edit anyone's comments, and can manage ratings. Moderators cannot administer user profiles.
- **Admin:** has full CRUD access to all content, can ban users (`PATCH /api/users/{id}/ban`), change roles to create moderators or admins (`PATCH /api/users/{id}/role`), and force-delete malicious accounts.
- _Critical requirement:_ The first user registered in the database (ID 1) is automatically assigned the **Admin** role and marked as verified.

## Security and Infrastructure Features

1. **Rate limiting (Slowapi):** Content creation endpoints (photos, comments, ratings, and search) and authentication endpoints are rate-limited through Redis sessions to help mitigate DDoS attacks and brute-force attempts.
2. **Email verification:** Two-step registration uses verification tokens. The full password recovery flow is available (`/request_password_reset` and `/reset_password/{token}`).
3. **Docker security:** The final `Dockerfile` is based on a hardened Alpine image, upgrades system components to address High/Critical vulnerabilities, and uses `.dockerignore` to minimize image size.