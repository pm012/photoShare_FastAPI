import pytest
from playwright.sync_api import Page, expect

from tests.ui.pages.feed_page import PhotoFeedPage
from tests.ui.pages.login_page import LoginPage

pytestmark = pytest.mark.auth


def test_login_with_wrong_password_shows_error(page: Page, data):
    user = data.user()
    login = LoginPage(page).open()

    login.login(user.email, "definitely-wrong-password")

    expect(login.error).to_contain_text("Invalid email or password")
    expect(login.submit_button).to_be_visible()  # still on the login screen


def test_login_with_valid_credentials_opens_the_gallery(page: Page, data):
    user = data.user()
    login = LoginPage(page).open()

    login.login(user.email, user.password)

    feed = PhotoFeedPage(page)
    expect(feed.gallery_tab).to_be_visible()
    expect(login.submit_button).to_have_count(0)


def test_banned_user_cannot_log_in(page: Page, data):
    user = data.user(is_active=False)
    login = LoginPage(page).open()

    login.login(user.email, user.password)

    expect(login.error).to_contain_text("banned")


def test_logout_returns_to_the_login_screen(open_as, data):
    page = open_as(data.user())
    feed = PhotoFeedPage(page)

    feed.logout()

    expect(LoginPage(page).submit_button).to_be_visible()
    assert page.evaluate("localStorage.getItem('token')") is None
