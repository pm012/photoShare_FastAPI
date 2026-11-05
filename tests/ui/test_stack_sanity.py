"""Proves the whole chain works: seeding -> token login -> real UI -> cleanup."""
import pytest
from playwright.sync_api import expect

from tests.ui.pages.feed_page import PhotoFeedPage

pytestmark = pytest.mark.smoke


def test_seeded_photo_is_found_and_rendered_in_the_feed(open_as, data, namer):
    owner = data.user()
    keyword = namer.word()
    photo = data.photo(owner, description=f"sunset {keyword}")
    page = open_as(owner)
    feed = PhotoFeedPage(page)

    feed.search(keyword)

    expect(feed.card(photo.id)).to_be_visible()
    expect(feed.cards).to_have_count(1)  # the shared feed is filtered down to this test's data
    page.wait_for_function("img => img.complete && img.naturalWidth > 0", arg=feed.card_image(photo.id).element_handle())


def test_cleanup_removes_everything_the_test_created(data):
    author = data.user("moderator")
    other = data.user()
    photo = data.photo(author, description="to be removed", tags=("e2e_cleanup_probe_tag",))
    comment_id = data.comment(photo, other, "hello")
    data.rating(photo, other, 5)
    assert data.photo_row(photo.id)["tags"] == ["e2e_cleanup_probe_tag"]
    assert data.comments_of(photo.id) == ["hello"]
    assert data.ratings_of(photo.id) == [5]

    data.cleanup()

    assert data.user_row(author.id) is None and data.user_row(other.id) is None
    assert data.photo_row(photo.id) is None
    assert data.comments_of(photo.id) == [] and data.ratings_of(photo.id) == []
    assert comment_id  # created before cleanup


def test_stack_reports_the_dedicated_e2e_database(stack_ready, settings):
    assert stack_ready["e2e"] is True
    assert stack_ready["database"].endswith("_e2e")
