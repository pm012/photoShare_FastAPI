"""Readiness check: waits for the stack and proves it is the disposable e2e stack."""
import time
from urllib.parse import urlsplit

import httpx


class StackError(RuntimeError):
    pass


def wait_for_stack(backend_url: str, base_url: str, database_url: str | None, timeout: float = 120) -> dict:
    deadline = time.monotonic() + timeout
    last = "nothing answered yet"
    while time.monotonic() < deadline:
        try:
            info = httpx.get(f"{backend_url}/e2e/info", timeout=5)
            if info.status_code == 404:
                raise StackError(
                    f"{backend_url} is running WITHOUT E2E_MODE. Refusing to run UI tests against it. "
                    "Start the disposable stack: docker compose -f docker-compose.e2e.yaml up -d --build"
                )
            frontend = httpx.get(base_url, timeout=5)
            if info.status_code == 200 and frontend.status_code == 200:
                data = info.json()
                expected_db = urlsplit(database_url).path.lstrip("/") if database_url else None
                if expected_db and data.get("database") != expected_db:
                    raise StackError(
                        f"Backend uses database '{data.get('database')}', but the tests seed '{expected_db}'."
                    )
                return data
            last = f"backend /e2e/info -> {info.status_code}, frontend -> {frontend.status_code}"
        except httpx.HTTPError as exc:
            last = repr(exc)
        time.sleep(2)
    raise StackError(f"Stack was not ready after {timeout:.0f}s ({last}).")
