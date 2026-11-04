"""Settings and safety guards for the Playwright UI suite.

Values come from (highest priority first): shell/CI environment, tests/ui/.env.e2e, defaults.
Everything is prefixed with E2E_ (E2E_BASE_URL, E2E_API_URL, E2E_DATABASE_URL, ...).
"""
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).with_name(".env.e2e")

# The e2e database must be dedicated to tests. Test data is created and deleted there,
# so we refuse to touch any database that is not clearly marked as such.
SAFE_DB_SUFFIX = "_e2e"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "db", "postgres"}


class E2ESettings(BaseSettings):
    base_url: str = "http://localhost:5173"
    api_url: str = "http://localhost:8000/api"
    database_url: str | None = None
    # Set to true only for a dedicated, disposable remote database (e.g. a CI service).
    allow_remote_db: bool = False

    model_config = SettingsConfigDict(
        env_prefix="E2E_", env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def backend_url(self) -> str:
        """API root without the /api prefix (for /health and similar endpoints)."""
        url = self.api_url.rstrip("/")
        return url[: -len("/api")] if url.endswith("/api") else url


@lru_cache
def get_settings() -> E2ESettings:
    return E2ESettings()


def assert_safe_database(url: str | None, allow_remote: bool = False) -> str:
    """Return `url` if it points to a dedicated e2e database, otherwise raise.

    Called before any test data is written, so a wrong .env can never make the suite
    create or delete rows in a development or production database.
    """
    if not url:
        raise RuntimeError(
            "E2E_DATABASE_URL is not set. Point it to a dedicated database whose name "
            f"ends with '{SAFE_DB_SUFFIX}' (see tests/ui/.env.e2e.sample)."
        )
    parts = urlsplit(url)
    db_name = parts.path.lstrip("/")
    if not db_name.endswith(SAFE_DB_SUFFIX):
        raise RuntimeError(
            f"Refusing to run: database '{db_name}' does not end with '{SAFE_DB_SUFFIX}'."
        )
    if parts.hostname not in LOCAL_HOSTS and not allow_remote:
        raise RuntimeError(
            f"Refusing to run: database host '{parts.hostname}' is not local. "
            "Set E2E_ALLOW_REMOTE_DB=true only for a disposable CI database."
        )
    return url
