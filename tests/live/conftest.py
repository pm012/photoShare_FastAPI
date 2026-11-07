"""Fixtures for the post-deploy smoke checks (see .github/workflows/live-smoke.yml)."""
import os
import time

import httpx
import pytest
from playwright.sync_api import expect


@pytest.fixture(scope="session")
def live_urls() -> dict:
    base = os.environ.get("LIVE_BASE_URL", "").rstrip("/")
    api = os.environ.get("LIVE_API_URL", "").rstrip("/")
    if not base or not api:
        pytest.exit("Set LIVE_BASE_URL (frontend) and LIVE_API_URL (backend, ending in /api).", returncode=2)
    return {"base": base, "api": api, "root": api.removesuffix("/api")}


@pytest.fixture(scope="session", autouse=True)
def backend_awake(live_urls: dict) -> float:
    """Free Render services go to sleep when idle and need up to a few minutes to wake up:
    poll /health until the backend answers, and only then start the tests."""
    timeout = float(os.environ.get("LIVE_WAKE_TIMEOUT", "300"))
    started = time.monotonic()
    last = "no answer yet"
    while time.monotonic() - started < timeout:
        try:
            response = httpx.get(f"{live_urls['root']}/health", timeout=30)
            if response.status_code == 200:
                return time.monotonic() - started
            last = f"HTTP {response.status_code}"
        except httpx.HTTPError as exc:
            last = type(exc).__name__
        time.sleep(10)
    pytest.exit(f"Backend did not wake up within {timeout:.0f}s ({last}).", returncode=2)


@pytest.fixture(scope="session")
def base_url(live_urls: dict) -> str:
    return live_urls["base"]


@pytest.fixture(scope="session", autouse=True)
def _expect_timeout():
    expect.set_options(timeout=20_000)  # a freshly woken service is slow on the first requests
