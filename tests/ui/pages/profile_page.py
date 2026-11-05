from pathlib import Path

from playwright.sync_api import Locator, Page

from .base_page import BasePage


class ProfilePage(BasePage):
    """Own profile (Profile.jsx + AvatarUpload.jsx)."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.username = page.locator(".pi-username")
        self.edit_username_button = self.by_id("profile-username-edit")
        self.username_input = self.by_id("profile-username")
        self.save_username_button = self.by_id("profile-username-save")
        self.cancel_username_button = self.by_id("profile-username-cancel")
        self.avatar_button = self.by_id("profile-avatar-upload")
        self.avatar_file_input = self.by_id("profile-avatar-file")
        self.avatar_preview = self.by_id("profile-avatar-preview")
        self.delete_avatar_button = self.by_id("profile-avatar-delete")
        self.avatar_error = page.locator(".av-error")
        self.my_photos_header = page.get_by_role("heading", name="My photos")

    def value_of(self, label: str) -> Locator:
        """Value cell of a row in the info list, e.g. value_of("Email"), value_of("Role")."""
        row = self.page.locator(".pi-row").filter(has=self.page.locator("dt", has_text=label))
        return row.locator("dd")

    def rename(self, new_username: str) -> None:
        self.edit_username_button.click()
        self.username_input.fill(new_username)
        self.save_username_button.click()

    def upload_avatar(self, path: str | Path) -> None:
        self.avatar_file_input.set_input_files(str(path))

    def delete_avatar(self) -> None:
        self.click_and_confirm(self.delete_avatar_button)

    def photo_tile(self, photo_id: int) -> Locator:
        return self.by_id(f"profile-photo-{photo_id}")
