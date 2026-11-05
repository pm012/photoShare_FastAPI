from playwright.sync_api import Locator, Page


class BasePage:
    """Common helpers. Locators are created lazily, so they stay valid across navigations.

    `by_id("x")` finds `id="x"`: conftest.py maps Playwright's test-id attribute to `id`.
    """

    path = "/"

    def __init__(self, page: Page):
        self.page = page

    # kept for backwards compatibility with the first tests
    def navigate_to(self, url: str):
        self.page.goto(url)

    def open(self):
        self.page.goto(self.path)
        return self

    def by_id(self, element_id: str) -> Locator:
        return self.page.get_by_test_id(element_id)

    @property
    def error(self) -> Locator:
        """The visible error banner (role=alert)."""
        return self.page.get_by_role("alert")

    @property
    def success(self) -> Locator:
        """The visible success banner (role=status)."""
        return self.page.get_by_role("status")

    # window.confirm() is auto-DISMISSED by Playwright unless a handler is registered first.
    def confirm_next_dialog(self) -> None:
        self.page.once("dialog", lambda dialog: dialog.accept())

    def dismiss_next_dialog(self) -> None:
        self.page.once("dialog", lambda dialog: dialog.dismiss())

    def click_and_confirm(self, locator: Locator) -> None:
        self.confirm_next_dialog()
        locator.click()
