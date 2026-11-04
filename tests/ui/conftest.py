"""Shared fixtures for the Playwright UI suite.

The `page`, `context`, `browser` fixtures come from pytest-playwright: every test gets a
fresh browser context, so cookies/localStorage never leak between tests.
Fixtures that create data in the database are added in step 2.
"""
import pytest

from tests.ui.config import E2ESettings, get_settings
from tests.ui.support.naming import Namer


@pytest.fixture(scope="session")
def settings() -> E2ESettings:
    return get_settings()


@pytest.fixture(scope="session")
def base_url(pytestconfig, settings: E2ESettings) -> str:
    """Priority: --base-url / PYTEST_BASE_URL  >  E2E_BASE_URL (.env.e2e)  >  default."""
    return pytestconfig.getoption("base_url") or settings.base_url


@pytest.fixture(scope="session", autouse=True)
def _use_id_as_test_id(playwright):
    """Lets `page.get_by_test_id("feed-upload-photo")` use the existing id="..." attributes,
    so the React code needs no data-testid changes."""
    playwright.selectors.set_test_id_attribute("id")


@pytest.fixture(scope="session")
def namer() -> Namer:
    """One per pytest session (= one per xdist worker)."""
    return Namer()
