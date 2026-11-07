# PhotoShare FastAPI: REST API | React | Playwright
- Unittests (Pytest) results: ![Photo Share Unit Tests](https://github.com/pm012/photoShare_FastAPI/actions/workflows/ci.yml/badge.svg)

- UI tests (Playwright) results: ![Photo Share UI Tests](https://github.com/pm012/photoShare_FastAPI/actions/workflows/e2e.yml/badge.svg)




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
Open separate terminal and run

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


# UI tests (Playwright + pytest)

Browser tests for the React frontend, running against a **disposable** stack. They are completely separate from the
unit tests: own pytest config (`tests/ui/pytest.ini`), never collected by `poetry run pytest`, never part of the
`CI Pipeline` workflow.

## Quick start

```bash
poetry install --with dev,e2e && poetry run playwright install chromium     # once
docker compose -f docker-compose.e2e.yaml up -d --build                     # stack: :5183 :8010 :5434 :6380
poetry run pytest tests/ui -n 4                                              # everything, 4 browsers
docker compose -f docker-compose.e2e.yaml down -v                            # throw it all away
```

| Goal | Command |
|---|---|
| sequential run | `poetry run pytest tests/ui` |
| a group | `-m "auth or session"` (markers: smoke, auth, feed, photo, profile, admin, moderation, session, rbac) |
| one test, visible browser | `-k logout --headed --slowmo 300` |
| slowest tests | `--durations=15` |
| debug a failure | `poetry run playwright show-trace test-results/<test>/trace.zip` |
| framework self-checks only (no stack) | `-m framework` |
| slower machine | `E2E_EXPECT_TIMEOUT=12000 poetry run pytest tests/ui -n 2` |

Rebuild after changing `src/` or `frontend/`: add `--build` to `up`. `-n auto` is capped at 4 workers
(`--maxprocesses` in `pytest.ini`): more browsers than the single backend can serve only cause timeouts.

## How it works

```
tests/ui/
  pytest.ini         own pytest "project": rootdir here, pythonpath ../.., markers, xdist settings
  conftest.py        fixtures: stack check, db, data factory, open_as(user), image/token helpers
  config.py          E2E_* settings + the safety guard for the database name
  flows.py           multi-step navigations shared by tests
  pages/             Page Objects, one per screen (+ components/: header, upload dialog)
  support/           db seeding/cleanup, naming, API login helper, image + token generators, stack check
  test_*.py          the tests, one file per area
```

* **Locators** use the existing `id="..."` attributes through `page.get_by_test_id(...)`
  (`set_test_id_attribute("id")` in `conftest.py`) - no changes to the React code were needed.
* **Test data** is created directly in the e2e database through the application's own SQLAlchemy models
  (`data.user("admin")`, `data.photo(...)`, `data.photos(owner, 21, ...)`, `data.comment(...)`, `data.rating(...)`).
  Seeded users log in via a token placed in `localStorage` (`open_as(user)`), so only the tests of the login screen
  use the login form.
* **E2E mode of the backend** (`E2E_MODE=true`): rate limiter off, photos/avatars stored in a local folder instead of
  Cloudinary, no real e-mail, `/e2e/info` endpoint. The backend refuses to start in this mode unless its database
  name ends with `_e2e`.
* **Safety nets**, in order: the backend's `_e2e` check; the test run aborts unless the backend reports e2e mode and the
  same database the tests seed; every test deletes what it created; each session sweeps leftovers by name prefix;
  and the stack itself is throwaway (`down -v`).

## Rules for new tests (they also make parallel runs safe)

1. Create data only through the `data` fixture; names only from `namer`; never rely on existing rows.
2. The feed, user list and moderation list are shared by all workers: always narrow them to your own data
   (unique `namer.word()` keyword, creator filter, unique username) before asserting. Never assert a total count of an
   unfiltered list.
3. Log in with `open_as(user)`; do not share pages or tokens between tests.
4. `window.confirm` dialogs are dismissed by Playwright unless a handler exists: use `click_and_confirm(...)`.
5. Wait for results, not time: `expect(...)` auto-waits; never `sleep`.
6. Known application bugs are documented as `@pytest.mark.xfail(strict=True, raises=AssertionError, ...)`; the
   marker must be removed when the bug is fixed (the test then fails as "XPASS").

## CI

| Workflow | Runs | Purpose | Blocks merges? |
|---|---|---|---|
| `ci.yml` "CI Pipeline" | every push/PR to main | unit tests only | **yes** (the required check) |
| `e2e.yml` "UI Tests (Playwright)" | nightly 03:00 UTC, PRs touching app/test code, manually | full UI suite, `-n 2`, on a stack built from the commit | no |
| `live-smoke.yml` "Live Smoke (Render)" | daily 05:30 UTC, manually | optional read-only checks of the deployed site | no |

* Manual run with options: Actions -> "UI Tests (Playwright)" -> Run workflow (workers, extra pytest args like `-m smoke`).
* Every run uploads `ui-test-results` (traces, screenshots, JUnit, backend/frontend logs; 14 days) and writes a
  summary on the run page. A failing **nightly** run opens (or comments on) the issue "Nightly UI tests are failing".
* Scheduled workflows run only from the default branch and GitHub pauses them after 60 days without repository
  activity.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `Stack was not ready ... Connection refused` | stack not running -> `docker compose -f docker-compose.e2e.yaml up -d`; or a stale `tests/ui/.env.e2e` overrides the ports (delete it) |
| `running WITHOUT E2E_MODE` | you point at the dev stack, or the image is old -> `up -d --build` |
| passes with `-n 0`, fails with `-n 4` | a test touches shared data (rule 2) |
| many `ReadTimeout`s | too many workers for the machine -> lower `-n`, raise `E2E_EXPECT_TIMEOUT` |
| leftover rows | `down -v` (nothing persists); then check `psql ... select count(*) from users` is 0 after a run |


