from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import Page, Response, expect

from .base_page import BasePage
from .components.header import Header
from .components.upload_dialog import UploadDialog


def _is_photo_search(response: Response) -> bool:
    return "/search/photos" in response.url and response.request.method == "GET"


def _search_with(param: str, text: str):
    """Predicate: a photo-search response whose query string has <param>=<text> (or no <param>)."""
    def predicate(response: Response) -> bool:
        if not _is_photo_search(response):
            return False
        value = parse_qs(urlsplit(response.url).query).get(param, [""])[0]
        return value == text
    return predicate


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
        self.empty_reset_button = self.by_id("feed-empty-reset-filters")
        self.page_label = page.get_by_label("Pagination").locator("span")
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
    def search(self, text: str, field: str = "description") -> None:
        """Choose the search field ("description" | "tag"), type `text` (350 ms debounce) and wait for
        the response that carries exactly this search. Typing the text that is already there sends no request."""
        self.search_field.select_option(field)
        param = "keyword" if field == "description" else "tag"
        with self.page.expect_response(_search_with(param, text)):
            self.search_input.fill(text)
        self.wait_until_loaded()

    def set_min_rating(self, value: str) -> None:
        """value = "" (any) | "4" | "3" | "2" """
        with self.reload_results():
            self.min_rating.select_option(value)
        self.wait_until_loaded()

    def go_next(self) -> None:
        with self.reload_results():
            self.next_page.click()
        self.wait_until_loaded()

    def go_previous(self) -> None:
        with self.reload_results():
            self.previous_page.click()
        self.wait_until_loaded()

    def card_ids(self) -> list[int]:
        return [int(card.get_attribute("id").removeprefix("photo-card-")) for card in self.cards.all()]

    def card_rating(self, photo_id: int):
        return self.card(photo_id).locator(".photo-rating")

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
