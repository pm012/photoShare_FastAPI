from playwright.sync_api import Page

from .base_page import BasePage


class LoginPage(BasePage):
    """Sign in / sign up / forgot password / reset password (Login.jsx)."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.title = page.get_by_role("heading", level=1)
        self.username_input = self.by_id("auth-username")
        self.email_input = self.by_id("auth-email")
        self.password_input = self.by_id("auth-password")
        self.confirm_password_input = self.by_id("auth-confirm-password")
        self.password_toggle = self.by_id("auth-password-toggle")
        self.submit_button = self.by_id("auth-submit")
        self.forgot_password_link = self.by_id("auth-forgot-password")
        self.create_account_button = self.by_id("auth-create-account")
        self.sign_in_link = self.by_id("auth-sign-in")
        self.back_to_sign_in_link = self.by_id("auth-back-to-sign-in")
        self.error_alert = self.error  # name used by the first tests

    def login(self, email: str, password: str) -> None:
        self.email_input.fill(email)
        self.password_input.fill(password)
        self.submit_button.click()

    def go_to_signup(self) -> None:
        self.create_account_button.click()

    def signup(self, username: str, email: str, password: str, confirm: str | None = None) -> None:
        self.go_to_signup()
        self.username_input.fill(username)
        self.email_input.fill(email)
        self.password_input.fill(password)
        self.confirm_password_input.fill(password if confirm is None else confirm)
        self.submit_button.click()

    def request_password_reset(self, email: str) -> None:
        self.forgot_password_link.click()
        self.email_input.fill(email)
        self.submit_button.click()

    def set_new_password(self, password: str, confirm: str | None = None) -> None:
        """On the reset screen (open `/?reset_token=<token>` first)."""
        self.password_input.fill(password)
        self.confirm_password_input.fill(password if confirm is None else confirm)
        self.submit_button.click()
