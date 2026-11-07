"""What happens when the session ends without the user pressing "Log out"."""
import pytest
from playwright.sync_api import Page, expect

from tests.ui.flows import goto_profile
from tests.ui.pages.login_page import LoginPage

pytestmark = pytest.mark.session


def test_invalid_token_sends_the_user_to_the_login_screen(page: Page):
    page.add_init_script("localStorage.setItem('token', 'garbage-token')")

    page.goto("/")

    expect(LoginPage(page).submit_button).to_be_visible()
    assert page.evaluate("localStorage.getItem('token')") is None


def test_user_banned_while_logged_in_is_signed_out_on_the_next_request(open_as, data):
    user = data.user()
    page = open_as(user)

    data.update_user(user.id, is_active=False)
    page.get_by_test_id("nav-profile").click()  # any API call will now answer "banned"

    expect(LoginPage(page).submit_button).to_be_visible()


def test_deleted_user_is_signed_out_on_the_next_request(open_as, data):
    user = data.user()
    page = open_as(user)
    data.cleanup()  # The account disappears while the browser is still logged in

    page.get_by_test_id("nav-profile").click()

    expect(LoginPage(page).submit_button).to_be_visible()


def test_inactive_user_is_logged_out_after_twenty_minutes(open_as, data):
    page = open_as(data.user(), fake_clock=True)

    page.clock.fast_forward(21 * 60 * 1000)

    expect(LoginPage(page).submit_button).to_be_visible()
    assert page.evaluate("localStorage.getItem('token')") is None


def test_logged_in_user_keeps_the_session_after_a_page_reload(open_as, data):
    page = open_as(data.user())

    page.reload()

    expect(page.get_by_test_id("nav-logout")).to_be_visible()
    goto_profile(page)  # and the API still accepts the token
