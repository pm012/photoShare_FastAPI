"""Shared fixtures for the Playwright UI suite.

Fixture map
  settings, base_url, namer     configuration and collision-free names
  stack_ready                   waits for the stack and proves it is the disposable e2e stack
  db                            e2e database (guarded); swept of this session's leftovers at the end
  anchor_user                   permanent user for the session, so UI sign-ups are never "the first user"
  data                          factory for users/photos/comments/ratings; cleans up after each test
  open_as(user)                 opens the app already logged in as `user` (token injected, no login form)
  page / new_context / ...      from pytest-playwright (fresh browser context per test)

Parallel runs (pytest -n 4): every xdist worker is a separate pytest session with its own browser,
`namer` (names contain the worker id), `db` connection, `anchor_user` and sweep. Tests must therefore
create their own data and filter shared lists by a unique keyword / creator (see README_step4).
"""
import os

import pytest
from playwright.sync_api import expect

from tests.ui.config import E2ESettings, assert_safe_database, get_settings
from tests.ui.support.api import Api
from tests.ui.support.db import Database, DataFactory
from tests.ui.support.images import make_image, make_large_png
from tests.ui.support.naming import Namer
from tests.ui.support.tokens import password_reset_token
from tests.ui.support.stack import StackError, wait_for_stack


# ----------------------------------------------------------------------------- start-up checks
def _only_framework_tests(config) -> bool:
    """True when the run selects nothing but the browser-less self-checks (no stack needed)."""
    if (config.getoption("markexpr") or "").strip() == "framework":
        return True
    paths = [arg for arg in config.args if not str(arg).startswith("-")]
    return bool(paths) and all("test_framework" in str(arg) for arg in paths)


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    """Check the stack ONCE, before any xdist worker is started, so a missing stack gives one clear
    message instead of one per worker. Workers skip this (they have `workerinput`)."""
    config = session.config
    if hasattr(config, "workerinput") or _only_framework_tests(config):
        return
    settings = get_settings()
    base = config.getoption("base_url") or settings.base_url
    try:
        wait_for_stack(settings.backend_url, base, settings.database_url)
    except StackError as exc:
        pytest.exit(str(exc), returncode=2)


@pytest.fixture(scope="session", autouse=True)
def _expect_timeout():
    """Auto-waiting assertions wait this long (ms). Parallel runs load the single backend harder, so
    the default can be raised without touching tests: E2E_EXPECT_TIMEOUT=10000 pytest tests/ui -n 4"""
    expect.set_options(timeout=float(os.environ.get("E2E_EXPECT_TIMEOUT", "7000")))


# ----------------------------------------------------------------------------- configuration
@pytest.fixture(scope="session")
def settings() -> E2ESettings:
    return get_settings()


@pytest.fixture(scope="session")
def base_url(pytestconfig, settings: E2ESettings) -> str:
    """Priority: --base-url / PYTEST_BASE_URL  >  E2E_BASE_URL (.env.e2e)  >  default."""
    return pytestconfig.getoption("base_url") or settings.base_url


@pytest.fixture(scope="session", autouse=True)
def _use_id_as_test_id(playwright):
    """`page.get_by_test_id("feed-upload-photo")` reads the existing id="..." attributes."""
    playwright.selectors.set_test_id_attribute("id")


@pytest.fixture(scope="session")
def namer() -> Namer:
    return Namer()


# ----------------------------------------------------------------------------- the stack
@pytest.fixture(scope="session")
def stack_ready(settings: E2ESettings, base_url: str) -> dict:
    try:
        return wait_for_stack(settings.backend_url, base_url, settings.database_url)
    except StackError as exc:
        pytest.exit(str(exc), returncode=2)


@pytest.fixture(autouse=True)
def _require_stack(request):
    """Every test except the browser-less `framework` self-checks needs the e2e stack."""
    if request.node.get_closest_marker("framework"):
        return
    request.getfixturevalue("stack_ready")


# ----------------------------------------------------------------------------- data
@pytest.fixture(scope="session")
def db(settings: E2ESettings, namer: Namer, stack_ready):
    url = assert_safe_database(settings.database_url, settings.allow_remote_db)
    database = Database(url, prefix=namer.prefix)
    yield database
    database.sweep()      # safety net: anything of this session that a test forgot to remove
    database.dispose()


@pytest.fixture(scope="session")
def anchor_user(db: Database, namer: Namer):
    """Without it a UI sign-up on an empty database would become the first user = admin."""
    factory = DataFactory(db, namer, base_url="")
    user = factory.user("user", label="anchor")
    yield user  # removed by db.sweep() (name prefix)


@pytest.fixture
def data(db: Database, namer: Namer, anchor_user, base_url: str):
    factory = DataFactory(db, namer, base_url=base_url)
    yield factory
    factory.cleanup()


# ----------------------------------------------------------------------------- authentication
@pytest.fixture(scope="session")
def api(settings: E2ESettings, base_url: str) -> Api:
    return Api(settings.api_url, base_url)


@pytest.fixture
def open_as(new_context, api: Api):
    """open_as(user) -> Page already logged in as that user, on the photo feed.

    A fresh token is requested per call: logging out blacklists a token, so tokens are never shared.
    """
    from playwright.sync_api import expect  # local import keeps module import light

    def _open(user, path: str = "/", *, fake_clock: bool = False):
        context = new_context(storage_state=api.storage_state(user.email, user.password))
        page = context.new_page()
        if fake_clock:  # lets a test jump forward in time (inactivity timeout)
            page.clock.install()
        page.goto(path)
        expect(page.get_by_test_id("nav-logout")).to_be_visible()
        return page

    return _open


# ----------------------------------------------------------------------------- files and tokens
@pytest.fixture
def png_file(tmp_path):
    return make_image(tmp_path / "photo.png", "PNG")


@pytest.fixture
def text_file(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("this is not an image")
    return path


@pytest.fixture
def fake_png_file(tmp_path):
    """Named .png (so the browser reports image/png) but the content is plain text."""
    path = tmp_path / "broken.png"
    path.write_text("definitely not a png")
    return path


@pytest.fixture
def large_png_file(tmp_path):
    return make_large_png(tmp_path / "large.png")


@pytest.fixture
def reset_token(settings):
    """reset_token(email) -> the token a "forgot password" e-mail would carry."""
    return lambda email: password_reset_token(email, settings.secret_key, settings.algorithm)
