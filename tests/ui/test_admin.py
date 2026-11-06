import pytest
from playwright.sync_api import expect

from tests.ui.flows import goto_admin
from tests.ui.pages.components.header import Header
from tests.ui.pages.login_page import LoginPage

pytestmark = pytest.mark.admin


@pytest.fixture
def as_admin(open_as, data):
    """(page, admin_user, AdminPage) of a freshly created administrator on the User Management screen."""
    admin_user = data.user("admin")
    page = open_as(admin_user)
    return page, admin_user, goto_admin(page)


# ----------------------------------------------------------------------------- searching
def test_admin_finds_a_user_by_username_and_by_email(as_admin, data):
    _, _, admin = as_admin
    target = data.user()

    admin.search(target.username)
    expect(admin.row(target.id)).to_contain_text(f"@{target.username}")
    expect(admin.row(target.id)).to_contain_text(target.email)

    admin.search(target.email)
    expect(admin.row(target.id)).to_be_visible()


def test_search_without_matches_says_so_and_can_be_cleared(as_admin, namer):
    _, _, admin = as_admin

    admin.search(namer.word("nobody"))
    expect(admin.empty_state).to_have_text("No users found.")

    admin.clear_button.click()
    expect(admin.search_input).to_have_value("")


def test_user_list_is_paginated(as_admin, data, namer):
    _, _, admin = as_admin
    marker = namer.word("pg")
    for _ in range(21):
        data.user(label=marker)

    admin.search(marker)
    expect(admin.rows).to_have_count(20)
    expect(admin.next_page).to_be_enabled()

    admin.go_next()
    expect(admin.rows).to_have_count(1)
    expect(admin.next_page).to_be_disabled()


# ----------------------------------------------------------------------------- administrator actions
def test_admin_can_ban_and_unban_a_user(as_admin, data, page):
    _, _, admin = as_admin
    target = data.user()
    admin.search(target.username)
    expect(admin.status_of(target.id)).to_have_text("Active")

    admin.toggle_ban(target.id)

    expect(admin.success).to_have_text("Changes are saved.")
    expect(admin.status_of(target.id)).to_have_text("Banned")
    expect(admin.ban_button(target.id)).to_have_text("Unban")
    assert data.user_row(target.id)["is_active"] is False
    login = LoginPage(page).open()  # a different browser context: the banned user tries to sign in
    login.login(target.email, target.password)
    expect(login.error).to_contain_text("banned")

    admin.toggle_ban(target.id)
    expect(admin.status_of(target.id)).to_have_text("Active")
    assert data.user_row(target.id)["is_active"] is True


def test_admin_can_make_a_user_a_moderator(as_admin, data, open_as):
    _, _, admin = as_admin
    target = data.user()
    admin.search(target.username)

    admin.change_role(target.id, "moderator")

    expect(admin.success).to_have_text("Changes are saved.")
    assert data.user_row(target.id)["role"] == "moderator"
    header = Header(open_as(target))  # the new role is effective at the next login
    expect(header.user_management).to_be_visible()
    expect(header.image_moderation).to_be_visible()


def test_admin_can_take_a_role_away_again(as_admin, data):
    _, _, admin = as_admin
    target = data.user("moderator")
    admin.search(target.username)

    admin.change_role(target.id, "user")

    expect(admin.success).to_have_text("Changes are saved.")
    assert data.user_row(target.id)["role"] == "user"


def test_admin_can_delete_a_user_with_all_their_content(as_admin, data):
    _, _, admin = as_admin
    target = data.user()
    photo = data.photo(target, description="goes away with the account")
    admin.search(target.username)

    admin.delete_user(target.id)

    expect(admin.row(target.id)).to_have_count(0)
    assert data.user_row(target.id) is None
    assert data.photo_row(photo.id) is None


def test_dismissing_the_delete_confirmation_keeps_the_user(as_admin, data):
    _, _, admin = as_admin
    target = data.user()
    admin.search(target.username)

    admin.dismiss_next_dialog()
    admin.delete_button(target.id).click()

    expect(admin.row(target.id)).to_be_visible()
    assert data.user_row(target.id) is not None


def test_admin_cannot_change_ban_or_delete_their_own_account(as_admin):
    _, admin_user, admin = as_admin
    admin.search(admin_user.username)

    expect(admin.row(admin_user.id)).to_be_visible()
    expect(admin.role_select(admin_user.id)).to_have_count(0)
    expect(admin.ban_button(admin_user.id)).to_be_disabled()
    expect(admin.delete_button(admin_user.id)).to_be_disabled()


def test_banned_users_are_marked_in_the_list(as_admin, data):
    _, _, admin = as_admin
    target = data.user(is_active=False)

    admin.search(target.username)

    expect(admin.status_of(target.id)).to_have_text("Banned")
    expect(admin.ban_button(target.id)).to_have_text("Unban")


def test_admin_screen_shows_the_administrator_badge(as_admin):
    _, _, admin = as_admin

    expect(admin.badge).to_have_text("Administrator")


# ----------------------------------------------------------------------------- moderator view
def test_moderator_can_look_at_users_but_not_manage_them(open_as, data):
    moderator, target = data.user("moderator"), data.user()
    admin = goto_admin(open_as(moderator))
    expect(admin.badge).to_have_text("Moderator")

    admin.search(target.username)

    expect(admin.row(target.id)).to_be_visible()
    expect(admin.role_select(target.id)).to_have_count(0)
    expect(admin.delete_button(target.id)).to_have_count(0)
    expect(admin.ban_button(target.id)).to_be_disabled()
    expect(admin.ban_button(target.id)).to_have_attribute("title", "Only administrators can ban users")
