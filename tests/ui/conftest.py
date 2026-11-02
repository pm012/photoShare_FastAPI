# Tells Pytest to discover and register Playwright fixtures
pytest_plugins = ["tests.ui.conftest"]
import pytest
from playwright.sync_api import expect
from tests.ui.pages.login_page import LoginPage
from tests.ui.pages.feed_page import PhotoFeedPage

def test_login_failure_shows_error_message(login_page: LoginPage):
    """Verifies that bad credentials display an error banner."""
    # Act
    login_page.login("invalid_user@test.com", "wrongpassword123")

    # Assert - Playwright auto-waits for the error element to populate
    expect(login_page.error_alert).to_be_visible()
    expect(login_page.error_alert).to_contain_text("Invalid")


def test_login_success_redirects_to_feed_and_logs_out(login_page: LoginPage, feed_page: PhotoFeedPage):
    """Verifies complete authentication cycle: success redirection, feed load, and logout."""
    # 1. Test Login Success
    # Act - Using backend seed credentials or mock test profile details
    login_page.login("alex@example.com", "securepassword123")

    # Assert - App header navigations and upload features become visible
    expect(feed_page.gallery_tab).to_be_visible()
    expect(feed_page.upload_button).to_be_visible()
    expect(feed_page.logout_button).to_be_visible()

    # 2. Test Logout Teardown
    # Act
    feed_page.logout()

    # Assert - User session context is cleanly destroyed, returning them to login view
    expect(login_page.submit_button).to_be_visible()
    expect(feed_page.logout_button).not_to_be_visible()
