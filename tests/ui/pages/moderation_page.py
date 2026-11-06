from playwright.sync_api import Locator, Page, expect

from .base_page import BasePage


class ModerationPage(BasePage):
    """Images Moderation (ModerationPanel.jsx), available to admins and moderators."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.creator_search = self.by_id("moderation-creator-search")
        self.creator_clear = self.by_id("moderation-creator-clear")
        self.description_search = self.by_id("moderation-search-description")
        self.sort = self.by_id("moderation-sort")      # date-desc | date-asc | rating-desc | rating-asc
        self.reset_button = self.by_id("moderation-reset-filters")
        self.next_page = self.by_id("moderation-next-page")
        self.previous_page = self.by_id("moderation-previous-page")
        self.dialog_close = self.by_id("moderation-dialog-close")
        self.creator_chip = page.locator(".mo-chip")
        self.rows = page.locator("table.mo-table tbody tr")
        self.empty_state = page.locator(".feed-status")
        self.section_title = page.locator(".mo-section-header h3")

    def row_of(self, photo_id: int) -> Locator:
        return self.page.get_by_role("row").filter(has=self.photo_image(photo_id))

    def pick_creator(self, user_id: int, typed: str) -> None:
        self.creator_search.fill(typed)
        self.by_id(f"moderation-creator-option-{user_id}").click()

    def photo_image(self, photo_id: int) -> Locator:
        return self.by_id(f"moderation-photo-image-{photo_id}")

    def open_photo(self, photo_id: int) -> Locator:
        """Opens the moderation dialog and returns it."""
        self.by_id(f"moderation-photo-{photo_id}-open").click()
        dialog = self.dialog(photo_id)
        # comments and ratings load separately; wait until both are in, so banners are unambiguous
        expect(dialog.get_by_text("Loading")).to_have_count(0)
        return dialog

    def dialog(self, photo_id: int) -> Locator:
        return self.by_id(f"moderation-photo-{photo_id}-dialog")

    def open_full_page(self, photo_id: int) -> None:
        self.by_id(f"moderation-photo-{photo_id}-open-page").click()

    def delete_comment(self, comment_id: int) -> None:
        self.click_and_confirm(self.by_id(f"moderation-comment-{comment_id}-delete"))

    def delete_rating(self, rating_id: int) -> None:
        self.click_and_confirm(self.by_id(f"moderation-rating-{rating_id}-delete"))
