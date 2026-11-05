from playwright.sync_api import Page

from .base_page import BasePage


class PhotoPageView(BasePage):
    """Single photo page (PhotoPage.jsx): details, rating, transformations, comments."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.back_button = self.by_id("photo-back-to-feed")
        self.image = self.by_id("photo-viewer-image")
        # These two exist only while the details editor is open (edit mode).
        self.description_input = self.by_id("photo-description")
        self.tags_input = self.by_id("photo-tags")
        self.score = page.locator(".pd-score")
        self.edit_details_button = self.by_id("photo-details-edit")
        self.save_details_button = self.by_id("photo-details-save")
        self.cancel_details_button = self.by_id("photo-details-cancel")
        self.delete_button = self.by_id("photo-delete")
        self.transform_preset = self.by_id("photo-transform-preset")
        self.transform_submit = self.by_id("photo-transform-submit")
        self.transformed_image = self.by_id("photo-transformed-image")
        self.qr_code = self.by_id("photo-transformation-qr")
        self.comment_input = self.by_id("photo-comment-input")
        self.comment_submit = self.by_id("photo-comment-submit")

    def author_link(self, photo_id: int):
        return self.by_id(f"photo-page-author-{photo_id}")

    # ---- rating -----------------------------------------------------------------
    def rating_button(self, value: int):
        return self.by_id(f"photo-rating-{value}")

    def rate(self, value: int) -> None:
        self.rating_button(value).click()

    # ---- details (owner or staff) -----------------------------------------------
    def edit_details(self, description: str | None = None, tags: str | None = None) -> None:
        """Opens the editor and fills the given fields. Click `save_details_button` afterwards."""
        self.edit_details_button.click()
        if description is not None:
            self.description_input.fill(description)
        if tags is not None:
            self.tags_input.fill(tags)

    def delete_photo(self) -> None:
        self.click_and_confirm(self.delete_button)

    # ---- comments -----------------------------------------------------------------
    def comment(self, text: str):
        """The comment article containing `text` (use for visibility/absence assertions)."""
        return self.page.locator("article.pd-comment").filter(has_text=text)

    def add_comment(self, text: str) -> None:
        self.comment_input.fill(text)
        self.comment_submit.click()

    def comment_edit_button(self, comment_id: int):
        return self.by_id(f"photo-comment-{comment_id}-edit")

    def comment_delete_button(self, comment_id: int):
        return self.by_id(f"photo-comment-{comment_id}-delete")

    def edit_comment(self, comment_id: int, new_text: str) -> None:
        self.comment_edit_button(comment_id).click()
        self.by_id(f"photo-comment-{comment_id}-edit-input").fill(new_text)
        self.by_id(f"photo-comment-{comment_id}-edit-save").click()

    def delete_comment(self, comment_id: int) -> None:
        self.click_and_confirm(self.comment_delete_button(comment_id))
