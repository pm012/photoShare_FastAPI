"""Readiness check: waits for the stack and proves it is the disposable e2e stack."""
import os
import time
from urllib.parse import urlsplit

import httpx


class StackError(RuntimeError):
    pass


class _NotReady(Exception):
    pass


def _get(url: str) -> httpx.Response:
    try:
        return httpx.get(url, timeout=5)
    except httpx.HTTPError as exc:
        raise _NotReady(f"{url} -> {type(exc).__name__}: {exc}") from exc


def wait_for_stack(backend_url: str, base_url: str, database_url: str | None,
                   timeout: float | None = None) -> dict:
    timeout = timeout or float(os.environ.get("E2E_STACK_TIMEOUT", "60"))
    deadline = time.monotonic() + timeout
    last = "nothing answered yet"
    while time.monotonic() < deadline:
        try:
            info = _get(f"{backend_url}/e2e/info")
            if info.status_code == 404:
                raise StackError(
                    f"{backend_url} is running WITHOUT E2E_MODE (or an outdated image). "
                    "Run: docker compose -f docker-compose.e2e.yaml up -d --build"
                )
            frontend = _get(base_url)
            if info.status_code == 200 and frontend.status_code == 200:
                data = info.json()
                expected_db = urlsplit(database_url).path.lstrip("/") if database_url else None
                if expected_db and data.get("database") != expected_db:
                    raise StackError(
                        f"Backend uses database '{data.get('database')}', but the tests seed '{expected_db}'."
                    )
                return data
            last = f"backend -> {info.status_code}, frontend -> {frontend.status_code}"
        except _NotReady as exc:
            last = str(exc)
        time.sleep(2)
    raise StackError(
        f"Stack was not ready after {timeout:.0f}s.\n"
        f"  Looked at: backend {backend_url}, frontend {base_url}\n"
        f"  Last problem: {last}\n"
        "  Check tests/ui/.env.e2e and E2E_* variables (they override the defaults), then:\n"
        "  docker compose -f docker-compose.e2e.yaml ps -a"
    )
