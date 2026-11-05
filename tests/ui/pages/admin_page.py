from playwright.sync_api import Locator, Page, Response

from .base_page import BasePage


def _is_user_search(response: Response) -> bool:
    return "/search/users" in response.url and response.request.method == "GET"


class AdminPage(BasePage):
    """User Management (AdminPanel.jsx), available to admins and moderators."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.search_input = self.by_id("admin-search-query")
        self.search_button = self.by_id("admin-search-submit")
        self.clear_button = self.by_id("admin-search-clear")
        self.next_page = self.by_id("admin-next-page")
        self.previous_page = self.by_id("admin-previous-page")
        self.table = page.locator("table.ad-table")
        self.access_denied = page.get_by_role("alert")

    def search(self, text: str) -> None:
        self.search_input.fill(text)
        with self.page.expect_response(_is_user_search):
            self.search_button.click()

    def row(self, user_id: int) -> Locator:
        """The table row of a user, found through its (unique) ban button."""
        return self.page.get_by_role("row").filter(has=self.by_id(f"admin-user-{user_id}-ban-toggle"))

    def role_select(self, user_id: int) -> Locator:
        return self.by_id(f"admin-user-{user_id}-role")

    def ban_button(self, user_id: int) -> Locator:
        return self.by_id(f"admin-user-{user_id}-ban-toggle")

    def delete_button(self, user_id: int) -> Locator:
        return self.by_id(f"admin-user-{user_id}-delete")

    def change_role(self, user_id: int, role: str) -> None:
        """role = "user" | "moderator" | "admin" """
        self.role_select(user_id).select_option(role)

    def toggle_ban(self, user_id: int) -> None:
        self.ban_button(user_id).click()

    def delete_user(self, user_id: int) -> None:
        self.click_and_confirm(self.delete_button(user_id))
