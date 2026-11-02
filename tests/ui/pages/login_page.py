from playwright.sync_api import Page
from .base_page import BasePage

class LoginPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        # Selectors matching exact input and button ids 
        self.email_input = page.locator("#auth-email")
        self.password_input = page.locator("#auth-password")
        self.submit_button = page.locator("#auth-submit")
        self.error_alert = page.locator(".error-message") # Class selector 
        self.create_account_button = page.locator("#auth-create-account")

    def login(self, email: str, password: str):
        self.email_input.fill(email)
        self.password_input.fill(password)
        self.submit_button.click()
