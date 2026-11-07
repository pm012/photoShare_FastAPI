import os

import httpx
import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.live

SMOKE_EMAIL = os.environ.get("LIVE_SMOKE_EMAIL", "")
SMOKE_PASSWORD = os.environ.get("LIVE_SMOKE_PASSWORD", "")


def test_backend_health_endpoint(live_urls):
    response = httpx.get(f"{live_urls['root']}/health", timeout=60)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_screen_renders(page: Page):
    page.goto("/")

    expect(page.get_by_role("heading", name="Sign in")).to_be_visible()
    expect(page.locator("#auth-submit")).to_be_enabled()


def test_unknown_account_is_rejected_by_the_real_backend(page: Page):
    """Exercises frontend -> backend -> database without needing an account."""
    page.goto("/")

    page.locator("#auth-email").fill("live-smoke-nobody@example.com")
    page.locator("#auth-password").fill("not-a-real-password-1")
    page.locator("#auth-submit").click()

    expect(page.get_by_role("alert")).to_contain_text("Invalid email or password")


@pytest.mark.skipif(not (SMOKE_EMAIL and SMOKE_PASSWORD), reason="LIVE_SMOKE_EMAIL / LIVE_SMOKE_PASSWORD are not set")
def test_smoke_account_can_sign_in_and_out(page: Page):
    page.goto("/")

    page.locator("#auth-email").fill(SMOKE_EMAIL)
    page.locator("#auth-password").fill(SMOKE_PASSWORD)
    page.locator("#auth-submit").click()
    expect(page.locator("#nav-gallery")).to_be_visible()

    page.locator("#nav-logout").click()
    expect(page.locator("#auth-submit")).to_be_visible()
