import re

import pytest
from playwright.sync_api import expect

from tests.ui.flows import goto_photo, goto_profile
from tests.ui.pages.feed_page import PhotoFeedPage
from tests.ui.pages.photo_page import PhotoPageView
from tests.ui.pages.public_profile_page import PublicProfilePage

pytestmark = pytest.mark.profile


def test_profile_shows_account_information_and_photos(open_as, data):
    user = data.user()
    photos = data.photos(user, 2, description="mine")
    profile = goto_profile(open_as(user))

    expect(profile.username).to_have_text(f"@{user.username}")
    expect(profile.value_of("Email")).to_have_text(user.email)
    expect(profile.value_of("Role")).to_have_text("User")
    expect(profile.value_of("Status")).to_contain_text("Active")
    expect(profile.value_of("Number of photos")).to_have_text("2")
    expect(profile.photo_tile(photos[0].id)).to_be_visible()
    expect(profile.photo_tile(photos[1].id)).to_be_visible()


def test_profile_of_a_moderator_shows_the_role(open_as, data):
    profile = goto_profile(open_as(data.user("moderator")))

    expect(profile.value_of("Role")).to_have_text("Moderator")


def test_profile_without_photos_shows_a_hint(open_as, data):
    profile = goto_profile(open_as(data.user()))

    expect(profile.page.get_by_text("You haven't uploaded any photos yet.")).to_be_visible()


def test_user_can_change_the_username(open_as, data, namer):
    user, new_name = data.user(), namer.username("renamed")
    profile = goto_profile(open_as(user))

    profile.rename(new_name)

    expect(profile.success).to_have_text("Username updated.")
    expect(profile.username).to_have_text(f"@{new_name}")
    assert data.user_row(user.id)["username"] == new_name


def test_username_that_is_already_taken_is_rejected(open_as, data):
    user, other = data.user(), data.user()
    profile = goto_profile(open_as(user))

    profile.rename(other.username)

    expect(profile.error).to_contain_text("Username already exists")
    assert data.user_row(user.id)["username"] == user.username


def test_empty_username_is_rejected(open_as, data):
    user = data.user()
    profile = goto_profile(open_as(user))

    profile.rename("")

    expect(profile.error).to_have_text("Username cannot be empty.")
    assert data.user_row(user.id)["username"] == user.username


def test_cancelling_the_rename_keeps_the_old_name(open_as, data):
    user = data.user()
    profile = goto_profile(open_as(user))

    profile.edit_username_button.click()
    profile.username_input.fill("something-else")
    profile.cancel_username_button.click()

    expect(profile.username).to_have_text(f"@{user.username}")


def test_user_can_upload_and_remove_an_avatar(open_as, data, png_file):
    user = data.user()
    profile = goto_profile(open_as(user))
    expect(profile.page.get_by_text("Click the circle to add a photo")).to_be_visible()

    profile.upload_avatar(png_file)

    expect(profile.success).to_have_text("Avatar updated.")
    expect(profile.avatar_preview).to_have_attribute("src", re.compile(r"/e2e-media/avatar_"))
    assert data.user_row(user.id)["avatar_url"]

    profile.delete_avatar()

    expect(profile.success).to_have_text("Avatar removed.")
    expect(profile.avatar_preview).to_have_count(0)
    assert data.user_row(user.id)["avatar_url"] is None


def test_avatar_rejects_unsupported_formats(open_as, data, text_file):
    profile = goto_profile(open_as(data.user()))

    profile.upload_avatar(text_file)

    expect(profile.avatar_error).to_have_text("Unsupported format. Choose PNG, JPG, or WEBP.")


def test_avatar_rejects_files_above_three_megabytes(open_as, data, large_png_file):
    profile = goto_profile(open_as(data.user()))

    profile.upload_avatar(large_png_file)

    expect(profile.avatar_error).to_have_text("File size must not exceed 3 MB.")


def test_clicking_one_of_my_photos_opens_its_page(open_as, data):
    user = data.user()
    photo = data.photo(user, description="open me")
    page = open_as(user)
    profile = goto_profile(page)

    profile.photo_tile(photo.id).click()

    expect(PhotoPageView(page).heading).to_have_text("open me")


# ----------------------------------------------------------------------------- public profile
def test_public_profile_lists_the_photos_of_another_user(open_as, data, namer):
    owner, viewer, keyword = data.user(), data.user(), namer.word()
    photos = data.photos(owner, 2, description=keyword)
    page = open_as(viewer)
    feed = PhotoFeedPage(page)
    feed.search(keyword)
    feed.open_author(photos[0].id)
    public = PublicProfilePage(page)

    expect(public.heading).to_have_text(f"@{owner.username}")
    expect(public.photo_count).to_have_text("2")
    expect(public.photo_tile(photos[0].id)).to_be_visible()
    expect(public.photo_tile(photos[1].id)).to_be_visible()

    public.photo_tile(photos[1].id).click()
    expect(PhotoPageView(page).heading).to_be_visible()


def test_public_profile_back_button_returns_to_the_feed(open_as, data, namer):
    owner, viewer, keyword = data.user(), data.user(), namer.word()
    photo = data.photo(owner, description=keyword)
    page = open_as(viewer)
    feed = PhotoFeedPage(page)
    feed.search(keyword)
    feed.open_author(photo.id)

    PublicProfilePage(page).back_button.click()

    expect(feed.upload_button).to_be_visible()


def test_public_profile_of_a_user_without_photos(open_as, data, namer):
    """Reached through a comment author link, since such a user has no photo in the feed."""
    owner, silent, keyword = data.user(), data.user(), namer.word()
    photo = data.photo(owner, description=keyword)
    comment_id = data.comment(photo, silent, "I only comment")
    page = open_as(data.user())
    view = goto_photo(page, photo, keyword)

    view.comment_author_link(comment_id).click()

    public = PublicProfilePage(page)
    expect(public.heading).to_have_text(f"@{silent.username}")
    expect(public.photo_count).to_have_text("0")
    expect(page.get_by_text("This user hasn't uploaded any photos yet.")).to_be_visible()
