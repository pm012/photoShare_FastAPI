from playwright.sync_api import Page


class Header:
    """Top navigation bar (App.jsx). Staff-only items exist only for admins/moderators."""

    def __init__(self, page: Page):
        self.brand = page.get_by_test_id("nav-brand")
        self.gallery = page.get_by_test_id("nav-gallery")
        self.user_management = page.get_by_test_id("nav-user-management")
        self.image_moderation = page.get_by_test_id("nav-image-moderation")
        self.profile = page.get_by_test_id("nav-profile")
        self.logout_button = page.get_by_test_id("nav-logout")

    def logout(self) -> None:
        self.logout_button.click()
