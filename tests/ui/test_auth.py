import pytest
from playwright.sync_api import Page, expect

from tests.ui.pages.feed_page import PhotoFeedPage
from tests.ui.pages.login_page import LoginPage

pytestmark = pytest.mark.auth
NEW_PASSWORD = "NewPassw0rd!e2e"


# ----------------------------------------------------------------------------- sign in / sign out
def test_login_with_wrong_password_shows_error(page: Page, data):
    user = data.user()
    login = LoginPage(page).open()

    login.login(user.email, "definitely-wrong-password")

    expect(login.error).to_contain_text("Invalid email or password")
    expect(login.submit_button).to_be_visible()  # still on the login screen


def test_login_with_unknown_email_shows_the_same_error(page: Page):
    login = LoginPage(page).open()

    login.login("nobody-here@example.com", "whatever-123")

    expect(login.error).to_contain_text("Invalid email or password")


def test_login_with_valid_credentials_opens_the_gallery(page: Page, data):
    user = data.user()
    login = LoginPage(page).open()

    login.login(user.email, user.password)

    expect(PhotoFeedPage(page).gallery_tab).to_be_visible()
    expect(login.submit_button).to_have_count(0)


def test_banned_user_cannot_log_in(page: Page, data):
    user = data.user(is_active=False)
    login = LoginPage(page).open()

    login.login(user.email, user.password)

    expect(login.error).to_contain_text("banned")


def test_logout_returns_to_the_login_screen(open_as, data):
    page = open_as(data.user())

    PhotoFeedPage(page).logout()

    expect(LoginPage(page).submit_button).to_be_visible()
    assert page.evaluate("localStorage.getItem('token')") is None


def test_password_can_be_shown_and_hidden(page: Page):
    login = LoginPage(page).open()
    login.password_input.fill("secret-123")
    expect(login.password_input).to_have_attribute("type", "password")

    login.password_toggle.click()
    expect(login.password_input).to_have_attribute("type", "text")

    login.password_toggle.click()
    expect(login.password_input).to_have_attribute("type", "password")


def test_user_can_switch_between_login_signup_and_forgot_password(page: Page):
    login = LoginPage(page).open()
    expect(login.title).to_have_text("Sign in")

    login.go_to_signup()
    expect(login.title).to_have_text("Create an account")
    login.sign_in_link.click()
    expect(login.title).to_have_text("Sign in")

    login.forgot_password_link.click()
    expect(login.title).to_have_text("Reset your password")
    login.back_to_sign_in_link.click()
    expect(login.title).to_have_text("Sign in")


# ----------------------------------------------------------------------------- sign up
def test_signup_creates_an_account_that_can_log_in(page: Page, data, namer):
    username, email = namer.username("new"), namer.email("new")
    data.track_username(username)  # created through the UI, so register it for cleanup
    login = LoginPage(page).open()

    login.signup(username, email, "Passw0rd!e2e")

    expect(login.success).to_contain_text("Registration complete")
    row = data.user_row(username=username)
    assert row is not None and row["role"] == "user"  # NOT promoted to admin
    login.login(email, "Passw0rd!e2e")
    expect(PhotoFeedPage(page).gallery_tab).to_be_visible()


def test_signup_with_mismatching_passwords_is_blocked(page: Page, data, namer):
    username, email = namer.username("mismatch"), namer.email("mismatch")
    login = LoginPage(page).open()

    login.signup(username, email, "Passw0rd!e2e", confirm="Different!e2e1")

    expect(login.error).to_have_text("Passwords do not match.")
    assert data.user_row(username=username) is None


def test_signup_with_an_existing_email_is_rejected(page: Page, data, namer):
    existing = data.user()
    login = LoginPage(page).open()

    login.signup(namer.username("dup"), existing.email, "Passw0rd!e2e")

    expect(login.error).to_contain_text("Account already exists")


def test_signup_with_an_existing_username_is_rejected(page: Page, data, namer):
    existing = data.user()
    login = LoginPage(page).open()

    login.signup(existing.username, namer.email("dup"), "Passw0rd!e2e")

    expect(login.error).to_contain_text("Account already exists")


# ----------------------------------------------------------------------------- password recovery
@pytest.mark.parametrize("known_email", [True, False], ids=["existing-account", "unknown-account"])
def test_forgot_password_gives_the_same_answer_for_any_email(page: Page, data, known_email):
    email = data.user().email if known_email else "nobody-here@example.com"
    login = LoginPage(page).open()

    login.request_password_reset(email)

    expect(login.success).to_contain_text("If an account with this email exists")


def test_password_can_be_reset_with_a_valid_link(page: Page, data, reset_token):
    user = data.user()
    login = LoginPage(page)
    page.goto(f"/?reset_token={reset_token(user.email)}")
    expect(login.title).to_have_text("Set a new password")

    login.set_new_password(NEW_PASSWORD)

    expect(login.success).to_contain_text("Password updated")
    login.login(user.email, NEW_PASSWORD)
    expect(PhotoFeedPage(page).gallery_tab).to_be_visible()


def test_old_password_stops_working_after_a_reset(page: Page, data, reset_token):
    user = data.user()
    login = LoginPage(page)
    page.goto(f"/?reset_token={reset_token(user.email)}")
    login.set_new_password(NEW_PASSWORD)
    expect(login.success).to_contain_text("Password updated")

    login.login(user.email, user.password)

    expect(login.error).to_contain_text("Invalid email or password")


def test_reset_with_a_broken_link_shows_an_error(page: Page):
    login = LoginPage(page)
    page.goto("/?reset_token=this-is-not-a-valid-token")

    login.set_new_password(NEW_PASSWORD)

    expect(login.error).to_contain_text("Invalid or expired reset token")


def test_reset_link_cannot_be_used_twice(page: Page, data, reset_token):
    user = data.user()
    token = reset_token(user.email)
    login = LoginPage(page)
    page.goto(f"/?reset_token={token}")
    login.set_new_password(NEW_PASSWORD)
    expect(login.success).to_contain_text("Password updated")

    page.goto(f"/?reset_token={token}")
    login.set_new_password("AnotherPassw0rd!1")

    expect(login.error).to_contain_text("Invalid or expired reset token")
