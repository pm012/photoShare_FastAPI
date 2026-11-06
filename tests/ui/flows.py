"""Small multi-step navigations shared by several test modules."""
from playwright.sync_api import Page, expect

from tests.ui.pages.admin_page import AdminPage
from tests.ui.pages.components.header import Header
from tests.ui.pages.feed_page import PhotoFeedPage
from tests.ui.pages.moderation_page import ModerationPage
from tests.ui.pages.photo_page import PhotoPageView
from tests.ui.pages.profile_page import ProfilePage


def goto_photo(page: Page, photo, keyword: str) -> PhotoPageView:
    """From the feed: search for the photo's unique keyword, then open its page."""
    feed = PhotoFeedPage(page)
    feed.search(keyword)
    feed.open_photo(photo.id)
    view = PhotoPageView(page)
    expect(view.back_button).to_be_visible()
    return view


def goto_admin(page: Page) -> AdminPage:
    Header(page).user_management.click()
    admin = AdminPage(page)
    expect(page.get_by_role("heading", name="Users Management")).to_be_visible()
    return admin


def goto_moderation(page: Page) -> ModerationPage:
    Header(page).image_moderation.click()
    moderation = ModerationPage(page)
    expect(page.get_by_role("heading", name="Image Moderation")).to_be_visible()
    return moderation


def goto_profile(page: Page) -> ProfilePage:
    Header(page).profile.click()
    profile = ProfilePage(page)
    expect(profile.username).to_be_visible()
    return profile
