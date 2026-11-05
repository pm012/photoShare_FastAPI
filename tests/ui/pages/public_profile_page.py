from playwright.sync_api import Locator, Page

from .base_page import BasePage


class PublicProfilePage(BasePage):
    """Another user's profile (PublicProfile.jsx)."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.back_button = self.by_id("public-profile-back")
        self.heading = page.get_by_role("heading", level=2)
        self.photo_count = page.locator(".pr-stat strong")

    def photo_tile(self, photo_id: int) -> Locator:
        return self.by_id(f"profile-photo-{photo_id}")
