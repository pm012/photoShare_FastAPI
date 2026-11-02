import pytest
from playwright.sync_api import Page, expect

# Explicitly import your page object framework classes
from tests.ui.pages.login_page import LoginPage
from tests.ui.pages.feed_page import PhotoFeedPage

# Define the fixtures locally inside the test file so discovery is guaranteed
@pytest.fixture
def login_page(page: Page) -> LoginPage:
    login_view = LoginPage(page)
    # Adjust port to where your local frontend runs
    login_view.navigate_to("http://localhost:5173")
    return login_view

@pytest.fixture
def feed_page(page: Page) -> PhotoFeedPage:
    return PhotoFeedPage(page)

# --- Your E2E Browser Test Cases ---

def test_login_failure_shows_error_message(login_page: LoginPage):
    """Verifies that bad credentials display an error banner."""
    # Act
    login_page.login("invalid_user@test.com", "wrongpassword123")

    # Assert
    expect(login_page.error_alert).to_be_visible()
    expect(login_page.error_alert).to_contain_text("Invalid")


def test_login_success_redirects_to_feed_and_logs_out(login_page: LoginPage, feed_page: PhotoFeedPage):
    """Verifies complete authentication cycle: success redirection, feed load, and logout."""
    # 1. Test Login Success
    # Act - Use valid mock credentials from your setup
    login_page.login("svk1205@gmail.com", "secret01")

    # Assert
    expect(feed_page.gallery_tab).to_be_visible()
    expect(feed_page.upload_button).to_be_visible()
    expect(feed_page.logout_button).to_be_visible()

    # 2. Test Logout Teardown
    # Act
    feed_page.logout()

    # Assert
    expect(login_page.submit_button).to_be_visible()
    expect(feed_page.logout_button).not_to_be_visible()
