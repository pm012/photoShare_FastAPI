"""Who sees which parts of the application."""
import pytest
from playwright.sync_api import expect

from tests.ui.pages.components.header import Header

pytestmark = pytest.mark.rbac


def test_regular_user_sees_only_gallery_and_profile(open_as, data):
    header = Header(open_as(data.user("user")))

    expect(header.gallery).to_be_visible()
    expect(header.profile).to_be_visible()
    expect(header.user_management).to_have_count(0)
    expect(header.image_moderation).to_have_count(0)


@pytest.mark.parametrize("role", ["moderator", "admin"])
def test_staff_see_management_and_moderation(open_as, data, role):
    header = Header(open_as(data.user(role)))

    expect(header.user_management).to_be_visible()
    expect(header.image_moderation).to_be_visible()


def test_navigation_menu_follows_a_role_change(open_as, data):
    user = data.user("user")
    page = open_as(user)
    expect(Header(page).user_management).to_have_count(0)

    data.update_user(user.id, role="moderator")
    page.reload()

    expect(Header(page).user_management).to_be_visible()
