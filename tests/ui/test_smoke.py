"""Needs a running stack (backend + frontend). Run: poetry run pytest tests/ui -m smoke"""
import httpx
import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.smoke


def test_backend_is_healthy(settings):
    response = httpx.get(f"{settings.backend_url}/health", timeout=10)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_screen_renders(page: Page):
    page.goto("/")  # relative: resolved against base_url
    expect(page.get_by_role("heading", name="Sign in")).to_be_visible()
    expect(page.get_by_test_id("auth-submit")).to_be_enabled()
