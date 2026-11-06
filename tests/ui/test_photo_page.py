import re

import pytest
from playwright.sync_api import expect

from tests.ui.flows import goto_photo
from tests.ui.pages.feed_page import PhotoFeedPage

pytestmark = pytest.mark.photo


@pytest.fixture
def scene(data, namer):
    """An owner, a second regular user, and a photo of the owner with a unique keyword."""
    owner, viewer, keyword = data.user(), data.user(), namer.word()
    tag = namer.tag()
    photo = data.photo(owner, description=f"scene {keyword}", tags=(tag,))
    return {"owner": owner, "viewer": viewer, "keyword": keyword, "tag": tag, "photo": photo}


def _open(open_as, data, scene, who="viewer"):
    """Open the scene's photo page as scene["viewer"] / scene["owner"] (by key) or as any seeded user."""
    page = open_as(scene[who] if isinstance(who, str) else who)
    return page, goto_photo(page, scene["photo"], scene["keyword"])


# ----------------------------------------------------------------------------- viewing and rating
def test_photo_page_shows_description_tags_author_and_no_ratings(open_as, data, scene):
    page, view = _open(open_as, data, scene)

    expect(view.heading).to_have_text(f"scene {scene['keyword']}")
    expect(page.locator(".pd-tag")).to_have_text(f"#{scene['tag']}")
    expect(view.author_link(scene["photo"].id)).to_contain_text(f"@{scene['owner'].username}")
    expect(view.score).to_contain_text("No ratings yet")


def test_other_user_can_rate_a_photo(open_as, data, scene):
    page, view = _open(open_as, data, scene)

    view.rate(4)

    expect(view.success).to_have_text("You rated this photo 4 out of 5.")
    expect(view.score).to_contain_text("4.0")
    expect(view.score).to_contain_text("1 rating")
    expect(view.rating_hint).to_have_text("Your rating: 4 out of 5")
    expect(view.rating_button(4)).to_have_attribute("aria-pressed", "true")
    assert data.ratings_of(scene["photo"].id) == [4]


def test_average_rating_includes_ratings_of_other_users(open_as, data, scene):
    data.rating(scene["photo"], data.user(), 2)
    page, view = _open(open_as, data, scene)
    expect(view.score).to_contain_text("2.0")

    view.rate(4)

    expect(view.score).to_contain_text("3.0")  # (2 + 4) / 2
    expect(view.score).to_contain_text("2 ratings")


def test_owner_cannot_rate_their_own_photo(open_as, data, scene):
    page, view = _open(open_as, data, scene, who="owner")

    expect(page.get_by_text("You cannot rate your own photos.")).to_be_visible()
    expect(view.rating_button(5)).to_have_count(0)


# ----------------------------------------------------------------------------- comments
def test_user_can_post_a_comment(open_as, data, scene):
    page, view = _open(open_as, data, scene)

    view.add_comment("What a lovely place!")

    expect(view.success).to_have_text("Comment added.")
    expect(view.comment("What a lovely place!")).to_be_visible()
    expect(view.comment_count).to_have_text("1")
    assert data.comments_of(scene["photo"].id) == ["What a lovely place!"]


def test_blank_comment_cannot_be_posted(open_as, data, scene):
    page, view = _open(open_as, data, scene)

    expect(view.comment_submit).to_be_disabled()
    view.comment_input.fill("    ")
    expect(view.comment_submit).to_be_disabled()


def test_comment_length_is_limited_to_500_characters(open_as, data, scene):
    page, view = _open(open_as, data, scene)

    view.comment_input.fill("x" * 600)

    assert len(view.comment_input.input_value()) == 500
    expect(page.get_by_text("500/500")).to_be_visible()


def test_user_can_edit_but_not_delete_their_own_comment(open_as, data, scene):
    comment_id = data.comment(scene["photo"], scene["viewer"], "first version")
    page, view = _open(open_as, data, scene)

    expect(view.comment_edit_button(comment_id)).to_be_visible()
    expect(view.comment_delete_button(comment_id)).to_have_count(0)
    view.edit_comment(comment_id, "second version")

    expect(view.success).to_have_text("Comment updated.")
    expect(view.comment("second version")).to_be_visible()
    assert data.comments_of(scene["photo"].id) == ["second version"]


def test_user_cannot_change_someone_elses_comment(open_as, data, scene):
    comment_id = data.comment(scene["photo"], scene["owner"], "owner's comment")
    page, view = _open(open_as, data, scene)

    expect(view.comment("owner's comment")).to_be_visible()
    expect(view.comment_edit_button(comment_id)).to_have_count(0)
    expect(view.comment_delete_button(comment_id)).to_have_count(0)


@pytest.mark.parametrize("role", ["moderator", "admin"])
def test_staff_can_delete_any_comment(open_as, data, scene, role):
    comment_id = data.comment(scene["photo"], scene["viewer"], "please remove me")
    staff = data.user(role)
    page, view = _open(open_as, data, scene, who=staff)

    view.delete_comment(comment_id)

    expect(view.success).to_have_text("Comment deleted.")
    expect(view.comment("please remove me")).to_have_count(0)
    assert data.comments_of(scene["photo"].id) == []


def test_dismissing_the_confirmation_keeps_the_comment(open_as, data, scene):
    comment_id = data.comment(scene["photo"], scene["viewer"], "still here")
    staff = data.user("moderator")
    page, view = _open(open_as, data, scene, who=staff)

    view.dismiss_next_dialog()
    view.comment_delete_button(comment_id).click()

    expect(view.comment("still here")).to_be_visible()
    assert data.comments_of(scene["photo"].id) == ["still here"]


# ----------------------------------------------------------------------------- managing the photo
def test_owner_can_change_description_and_tags(open_as, data, scene, namer):
    new_tag = namer.tag("new")
    data.track_tag(new_tag)
    page, view = _open(open_as, data, scene, who="owner")

    view.edit_details(description=f"renamed {scene['keyword']}", tags=new_tag)
    view.save_details_button.click()

    expect(view.success).to_have_text("Photo details updated.")
    expect(view.heading).to_have_text(f"renamed {scene['keyword']}")
    assert data.photo_row(scene["photo"].id) == {
        "id": scene["photo"].id, "description": f"renamed {scene['keyword']}", "tags": [new_tag]}


def test_details_editor_blocks_more_than_five_tags(open_as, data, scene):
    page, view = _open(open_as, data, scene, who="owner")

    view.edit_details(tags="a, b, c, d, e, f")

    expect(page.get_by_text("Remove 1 tag(s) to save")).to_be_visible()
    expect(view.save_details_button).to_be_disabled()


def test_cancelling_the_editor_discards_changes(open_as, data, scene):
    page, view = _open(open_as, data, scene, who="owner")

    view.edit_details(description="something else entirely")
    view.cancel_details_button.click()

    expect(view.heading).to_have_text(f"scene {scene['keyword']}")
    assert data.photo_row(scene["photo"].id)["description"] == f"scene {scene['keyword']}"


def test_owner_can_delete_the_photo_and_returns_to_the_feed(open_as, data, scene):
    page, view = _open(open_as, data, scene, who="owner")

    view.delete_photo()

    expect(PhotoFeedPage(page).upload_button).to_be_visible()
    assert data.photo_row(scene["photo"].id) is None


def test_dismissing_the_delete_confirmation_keeps_the_photo(open_as, data, scene):
    page, view = _open(open_as, data, scene, who="owner")

    view.dismiss_next_dialog()
    view.delete_button.click()

    expect(view.heading).to_be_visible()
    assert data.photo_row(scene["photo"].id) is not None


def test_other_users_get_no_management_controls(open_as, data, scene):
    page, view = _open(open_as, data, scene)

    expect(view.manage_section).to_have_count(0)
    expect(view.edit_details_button).to_have_count(0)
    expect(view.delete_button).to_have_count(0)


def test_moderators_cannot_edit_photos_but_admins_can(open_as, data, scene):
    """The photo page offers editing to the owner and to administrators only."""
    _, moderator_view = _open(open_as, data, scene, who=data.user("moderator"))
    expect(moderator_view.manage_section).to_have_count(0)

    _, admin_view = _open(open_as, data, scene, who=data.user("admin"))
    expect(admin_view.manage_section).to_be_visible()
    expect(admin_view.delete_button).to_be_visible()


# ----------------------------------------------------------------------------- transformations
@pytest.mark.parametrize("preset", ["thumbnail", "avatar", "black_white"])
def test_user_can_create_a_transformed_version_with_a_qr_code(open_as, data, scene, preset):
    page, view = _open(open_as, data, scene)

    view.choose_preset(preset)
    view.transform_submit.click()

    expect(view.success).to_have_text("Transformed photo created.")
    expect(view.transformed_image).to_have_attribute("src", re.compile(rf"\?preset={preset}$"))
    expect(view.qr_code).to_be_visible()
    qr_url = view.qr_code.get_attribute("href")
    assert "/e2e-media/" in qr_url
    assert page.request.get(qr_url).ok  # the QR code image really exists
