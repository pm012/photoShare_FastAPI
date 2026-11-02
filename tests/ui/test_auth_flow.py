import pytest
from playwright.sync_api import Page, expect
from tests.ui.pages.login_page import LoginPage
from tests.ui.pages.feed_page import PhotoFeedPage

@pytest.fixture
def login_page(page: Page) -> LoginPage:
    login_view = LoginPage(page)
    # Target port for your running application
    login_view.navigate_to("http://localhost:5173")
    return login_view

@pytest.fixture
def feed_page(page: Page) -> PhotoFeedPage:
    return PhotoFeedPage(page)

# --- Test Cases ---

def test_login_failure_shows_error_message(login_page: LoginPage):
    login_page.login("invalid_user@test.com", "wrongpassword123")
    expect(login_page.error_alert).to_be_visible()
    expect(login_page.error_alert).to_contain_text("Invalid")

def test_login_success_redirects_to_feed_and_logs_out(login_page: LoginPage, feed_page: PhotoFeedPage):
    login_page.login("svk1205@gmail.com", "secret01")
    expect(feed_page.gallery_tab).to_be_visible()
    
    feed_page.logout()
    expect(login_page.submit_button).to_be_visible()
