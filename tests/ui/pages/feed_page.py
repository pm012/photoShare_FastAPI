from playwright.sync_api import Page
from .base_page import BasePage

class PhotoFeedPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        # Structural navigation elements from App.jsx header (source file 2)
        self.brand_logo = page.locator("#nav-brand")
        self.gallery_tab = page.locator("#nav-gallery")
        self.profile_tab = page.locator("#nav-profile")
        self.logout_button = page.locator("#nav-logout")
        
        # Feed specific assets from PhotoFeed.jsx (source file 4)
        self.upload_button = page.locator("#feed-upload-photo")
        self.search_input = page.locator("#feed-search-query")

    def logout(self):
        self.logout_button.click()
