from playwright.sync_api import Page, Response, expect

from .base_page import BasePage
from .components.header import Header
from .components.upload_dialog import UploadDialog


def _is_photo_search(response: Response) -> bool:
    return "/search/photos" in response.url and response.request.method == "GET"


class PhotoFeedPage(BasePage):
    """Photo Gallery (PhotoFeed.jsx)."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.header = Header(page)
        self.upload_button = self.by_id("feed-upload-photo")
        self.search_field = self.by_id("feed-search-field")          # <select>: description | tag
        self.search_input = self.by_id("feed-search-query")
        self.min_rating = self.by_id("feed-min-rating")              # <select>: "", "4", "3", "2"
        self.reset_button = self.by_id("feed-reset-filters")
        self.sort_by_date = self.by_id("feed-sort-date")
        self.sort_by_rating = self.by_id("feed-sort-rating")
        self.next_page = self.by_id("feed-next-page")
        self.previous_page = self.by_id("feed-previous-page")
        self.retry_button = self.by_id("feed-retry")
        self.cards = page.locator("article[id^='photo-card-']")
        self.skeletons = page.locator(".photo-card--skeleton")
        self.empty_state = page.locator(".feed-status")
        self.lightbox = self.by_id("photo-lightbox-dialog")
        self.lightbox_close = self.by_id("photo-lightbox-close")
        # names used by the first tests
        self.gallery_tab = self.header.gallery
        self.profile_tab = self.header.profile
        self.logout_button = self.header.logout_button

    def logout(self) -> None:
        self.header.logout()

    # ---- loading ----------------------------------------------------------------
    def wait_until_loaded(self) -> None:
        expect(self.skeletons).to_have_count(0)

    def reload_results(self):
        """Context manager: `with feed.reload_results(): <action that triggers a search>`."""
        return self.page.expect_response(_is_photo_search)

    # ---- actions ----------------------------------------------------------------
    def search(self, text: str, field: str | None = None) -> None:
        """Type into the search box (350 ms debounce) and wait for the resulting request.
        `field` = "description" | "tag". Note: typing the same text again sends no request."""
        if field:
            self.search_field.select_option(field)
        with self.reload_results():
            self.search_input.fill(text)
        self.wait_until_loaded()

    def sort_by(self, option: str) -> None:
        """option = "date" | "rating" """
        with self.reload_results():
            self.by_id(f"feed-sort-{option}").click()
        self.wait_until_loaded()

    def open_upload_dialog(self) -> UploadDialog:
        self.upload_button.click()
        return UploadDialog(self.page)

    # ---- one card ---------------------------------------------------------------
    def card(self, photo_id: int):
        return self.by_id(f"photo-card-{photo_id}")

    def card_image(self, photo_id: int):
        return self.by_id(f"photo-image-{photo_id}")

    def open_photo(self, photo_id: int) -> None:
        self.by_id(f"photo-open-{photo_id}").click()

    def open_author(self, photo_id: int) -> None:
        self.by_id(f"photo-author-{photo_id}").click()

    def zoom(self, photo_id: int) -> None:
        self.by_id(f"photo-zoom-{photo_id}").click()

    def tag_button(self, photo_id: int, tag_name: str):
        return self.card(photo_id).get_by_role("button", name=f"#{tag_name}")
