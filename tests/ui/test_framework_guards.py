"""Self-checks of the framework (no browser, no running stack needed)."""
import pytest

from tests.ui.config import E2ESettings, assert_safe_database
from tests.ui.support.naming import Namer

pytestmark = pytest.mark.framework


@pytest.mark.parametrize("url", [
    "postgresql+psycopg2://postgres:pw@localhost:5434/photoshare_e2e",
    "postgresql+psycopg2://postgres:pw@db:5432/app_e2e",
])
def test_guard_accepts_dedicated_local_database(url):
    assert assert_safe_database(url) == url


@pytest.mark.parametrize("url", [
    None,
    "",
    "postgresql+psycopg2://postgres:pw@localhost:5433/photoshare_db",  # the dev database
    "sqlite:///:memory:",
])
def test_guard_rejects_everything_else(url):
    with pytest.raises(RuntimeError):
        assert_safe_database(url)


def test_guard_rejects_remote_host_unless_allowed():
    url = "postgresql://u:p@dpg-123.render.com:5432/photoshare_e2e"
    with pytest.raises(RuntimeError):
        assert_safe_database(url)
    assert assert_safe_database(url, allow_remote=True) == url


def test_default_database_url_matches_the_compose_file_and_passes_the_guard():
    assert assert_safe_database(E2ESettings().database_url)


def test_backend_url_strips_api_prefix():
    assert E2ESettings(api_url="http://localhost:8000/api").backend_url == "http://localhost:8000"
    assert E2ESettings(api_url="http://localhost:8000/api/").backend_url == "http://localhost:8000"


def test_namer_is_unique_and_within_model_limits():
    namer = Namer()
    names = {namer.username() for _ in range(50)} | {namer.email() for _ in range(50)}
    assert len(names) == 100
    assert all(len(namer.username("x" * 60)) <= 50 for _ in range(3))
    assert len(namer.tag("y" * 60)) <= 30
    assert "_" not in namer.word()
