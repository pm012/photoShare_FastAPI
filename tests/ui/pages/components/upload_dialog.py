from pathlib import Path

from playwright.sync_api import Page


class UploadDialog:
    """The "Upload a photo" modal (UploadPhoto.jsx)."""

    def __init__(self, page: Page):
        self.dialog = page.get_by_test_id("upload-dialog")
        self.file_input = page.get_by_test_id("photo-file")      # visually hidden <input type=file>
        self.dropzone = page.get_by_test_id("upload-dropzone")
        self.preview = page.get_by_test_id("upload-preview")
        self.description = page.get_by_test_id("upload-description")
        self.tags = page.get_by_test_id("upload-tags")
        self.submit_button = page.get_by_test_id("upload-submit")
        self.cancel_button = page.get_by_test_id("upload-cancel")
        self.close_button = page.get_by_test_id("upload-close")
        self.replace_button = page.get_by_test_id("upload-replace-file")
        self.remove_button = page.get_by_test_id("upload-remove-file")
        self.error = self.dialog.get_by_role("alert")

    def choose_file(self, path: str | Path) -> None:
        self.file_input.set_input_files(str(path))

    def fill(self, description: str | None = None, tags: str | None = None) -> None:
        if description is not None:
            self.description.fill(description)
        if tags is not None:
            self.tags.fill(tags)

    def submit(self) -> None:
        self.submit_button.click()
