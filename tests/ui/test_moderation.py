from datetime import datetime, timedelta

import pytest
from playwright.sync_api import expect

from tests.ui.flows import goto_moderation
from tests.ui.pages.components.header import Header
from tests.ui.pages.login_page import LoginPage
from tests.ui.pages.photo_page import PhotoPageView

pytestmark = pytest.mark.moderation


@pytest.fixture
def staged(data, namer):
    """A moderator plus a photo (unique keyword) that has one comment and one rating."""
    moderator, owner, commenter = data.user("moderator"), data.user(), data.user()
    keyword = namer.word()
    photo = data.photo(owner, description=f"under review {keyword}")
    comment_id = data.comment(photo, commenter, "questionable comment")
    rating_id = data.rating(photo, commenter, 4)
    return {"moderator": moderator, "owner": owner, "keyword": keyword, "photo": photo,
            "comment_id": comment_id, "rating_id": rating_id}


def _moderate(open_as, staged, who=None):
    page = open_as(who or staged["moderator"])
    moderation = goto_moderation(page)
    moderation.description_search.fill(staged["keyword"])
    expect(moderation.photo_image(staged["photo"].id)).to_be_visible()
    return page, moderation


# ----------------------------------------------------------------------------- finding photos
def test_moderator_filters_photos_by_creator(open_as, data):
    moderator, creator, other = data.user("moderator"), data.user(), data.user()
    mine = data.photos(creator, 2, description="creator photo")
    theirs = data.photo(other, description="someone else's photo")
    moderation = goto_moderation(open_as(moderator))

    moderation.pick_creator(creator.id, creator.username)

    expect(moderation.section_title).to_have_text(f"Photos by @{creator.username}")
    expect(moderation.photo_image(mine[0].id)).to_be_visible()
    expect(moderation.photo_image(mine[1].id)).to_be_visible()
    expect(moderation.photo_image(theirs.id)).to_have_count(0)


def test_moderator_searches_descriptions(open_as, data, namer):
    moderator, owner, keyword = data.user("moderator"), data.user(), namer.word()
    hit = data.photo(owner, description=f"findme {keyword}")
    miss = data.photo(owner, description="unrelated")
    moderation = goto_moderation(open_as(moderator))

    moderation.description_search.fill(keyword)

    expect(moderation.photo_image(hit.id)).to_be_visible()
    expect(moderation.photo_image(miss.id)).to_have_count(0)


def test_nothing_found_message(open_as, data, namer):
    moderation = goto_moderation(open_as(data.user("moderator")))

    moderation.description_search.fill(namer.word("nothing"))

    expect(moderation.empty_state).to_contain_text("No photos match these filters.")


def test_reset_clears_every_filter(open_as, data, namer):
    creator = data.user()
    data.photo(creator, description="x")
    moderation = goto_moderation(open_as(data.user("moderator")))
    expect(moderation.reset_button).to_be_disabled()
    moderation.pick_creator(creator.id, creator.username)
    moderation.description_search.fill(namer.word())

    moderation.reset_button.click()

    expect(moderation.creator_chip).to_have_count(0)
    expect(moderation.description_search).to_have_value("")
    expect(moderation.sort).to_have_value("date-desc")


def test_oldest_first_sorting(open_as, data):
    moderator, creator = data.user("moderator"), data.user()
    start = datetime(2024, 3, 1, 9, 0)
    photos = [data.photo(creator, description=f"p{i}", created_at=start + timedelta(days=i)) for i in range(3)]
    moderation = goto_moderation(open_as(moderator))
    moderation.pick_creator(creator.id, creator.username)
    first_image = moderation.rows.locator("img").first
    expect(first_image).to_have_attribute("id", f"moderation-photo-image-{photos[2].id}")  # newest first

    moderation.sort.select_option("date-asc")

    expect(first_image).to_have_attribute("id", f"moderation-photo-image-{photos[0].id}")


# ----------------------------------------------------------------------------- reviewing a photo
def test_review_dialog_lists_comments_and_ratings(open_as, staged):
    page, moderation = _moderate(open_as, staged)

    dialog = moderation.open_photo(staged["photo"].id)

    expect(dialog).to_contain_text("questionable comment")
    expect(dialog).to_contain_text("1 total")
    expect(dialog).to_contain_text("★ 4 / 5")


def test_moderator_deletes_a_comment(open_as, data, staged):
    page, moderation = _moderate(open_as, staged)
    dialog = moderation.open_photo(staged["photo"].id)
    expect(dialog).to_contain_text("questionable comment")

    moderation.delete_comment(staged["comment_id"])

    expect(moderation.success).to_have_text("Comment deleted.")
    expect(dialog).to_contain_text("This photo has no comments.")
    assert data.comments_of(staged["photo"].id) == []


def test_moderator_edits_a_comment(open_as, data, staged):
    page, moderation = _moderate(open_as, staged)
    dialog = moderation.open_photo(staged["photo"].id)
    comment_id = staged["comment_id"]

    moderation.by_id(f"moderation-comment-{comment_id}-edit").click()
    moderation.by_id(f"moderation-comment-{comment_id}-edit-input").fill("cleaned up")
    moderation.by_id(f"moderation-comment-{comment_id}-edit-save").click()

    expect(moderation.success).to_have_text("Comment updated.")
    expect(dialog).to_contain_text("cleaned up")
    assert data.comments_of(staged["photo"].id) == ["cleaned up"]


def test_moderator_deletes_a_rating_and_the_list_updates(open_as, data, staged):
    page, moderation = _moderate(open_as, staged)
    expect(moderation.row_of(staged["photo"].id)).to_contain_text("★ 4.0")
    dialog = moderation.open_photo(staged["photo"].id)

    moderation.delete_rating(staged["rating_id"])

    expect(moderation.success).to_have_text("Rating deleted.")
    expect(dialog).to_contain_text("This photo has no ratings.")
    assert data.ratings_of(staged["photo"].id) == []
    moderation.dialog_close.click()
    expect(moderation.row_of(staged["photo"].id)).to_contain_text("Not rated")


def test_dismissing_the_confirmation_keeps_the_rating(open_as, data, staged):
    page, moderation = _moderate(open_as, staged)
    moderation.open_photo(staged["photo"].id)

    moderation.dismiss_next_dialog()
    moderation.by_id(f"moderation-rating-{staged['rating_id']}-delete").click()

    assert data.ratings_of(staged["photo"].id) == [4]


def test_review_dialog_closes_with_its_button_and_with_escape(open_as, staged):
    page, moderation = _moderate(open_as, staged)
    dialog = moderation.open_photo(staged["photo"].id)
    moderation.dialog_close.click()
    expect(dialog).to_have_count(0)

    dialog = moderation.open_photo(staged["photo"].id)
    page.keyboard.press("Escape")
    expect(dialog).to_have_count(0)


def test_photo_page_can_be_opened_from_the_review_dialog(open_as, staged):
    page, moderation = _moderate(open_as, staged)
    moderation.open_photo(staged["photo"].id)

    moderation.open_full_page(staged["photo"].id)

    expect(PhotoPageView(page).heading).to_have_text(f"under review {staged['keyword']}")


def test_administrators_can_moderate_too(open_as, data, staged):
    page, moderation = _moderate(open_as, staged, who=data.user("admin"))

    dialog = moderation.open_photo(staged["photo"].id)

    expect(dialog).to_contain_text("questionable comment")


# ----------------------------------------------------------------------------- known defect
@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "BUG: ModerationPanel keeps its filters in a module-level variable (`savedFilters`) that survives "
    "log-out/log-in, so the next user inherits the previous user's creator filter. "
    "Remove this marker once the filters are cleared on logout."))
def test_filters_do_not_leak_to_the_next_user_who_logs_in(open_as, data):
    first, second, creator = data.user("moderator"), data.user("admin"), data.user()
    page = open_as(first)
    moderation = goto_moderation(page)
    moderation.pick_creator(creator.id, creator.username)
    expect(moderation.creator_chip).to_be_visible()

    Header(page).logout()
    LoginPage(page).login(second.email, second.password)
    moderation = goto_moderation(page)

    expect(moderation.creator_chip).to_have_count(0)
