from datetime import datetime, timedelta

import pytest
from playwright.sync_api import expect

from tests.ui.flows import goto_photo
from tests.ui.pages.feed_page import PhotoFeedPage
from tests.ui.pages.public_profile_page import PublicProfilePage

pytestmark = pytest.mark.feed
# The feed is shared by every test, so each test searches for a keyword that only its own photos contain.


def test_feed_shows_author_description_and_image(open_as, data, namer):
    owner, keyword = data.user(), namer.word()
    photo = data.photo(owner, description=f"sunset {keyword}")
    page = open_as(owner)
    feed = PhotoFeedPage(page)

    feed.search(keyword)

    card = feed.card(photo.id)
    expect(card).to_contain_text(f"@{owner.username}")
    expect(card).to_contain_text(f"sunset {keyword}")
    expect(feed.card_rating(photo.id)).to_have_text("Not rated yet")
    page.wait_for_function("img => img.complete && img.naturalWidth > 0", arg=feed.card_image(photo.id).element_handle())


def test_search_by_description_hides_other_photos(open_as, data, namer):
    owner, wanted, other = data.user(), namer.word("a"), namer.word("b")
    hit = data.photo(owner, description=f"mountain {wanted}")
    miss = data.photo(owner, description=f"river {other}")
    feed = PhotoFeedPage(open_as(owner))

    feed.search(wanted)

    expect(feed.card(hit.id)).to_be_visible()
    expect(feed.card(miss.id)).to_have_count(0)


def test_search_by_tag(open_as, data, namer):
    owner, tag = data.user(), namer.tag()
    tagged = data.photo(owner, description="has the tag", tags=(tag,))
    untagged = data.photo(owner, description="has no tag")
    feed = PhotoFeedPage(open_as(owner))

    feed.search(tag, field="tag")

    expect(feed.card(tagged.id)).to_be_visible()
    expect(feed.card(untagged.id)).to_have_count(0)


def test_clicking_a_tag_switches_to_a_tag_search(open_as, data, namer):
    owner, keyword, tag = data.user(), namer.word(), namer.tag()
    tagged = data.photo(owner, description=f"tagged {keyword}", tags=(tag,))
    plain = data.photo(owner, description=f"plain {keyword}")
    feed = PhotoFeedPage(open_as(owner))
    feed.search(keyword)
    expect(feed.cards).to_have_count(2)

    with feed.reload_results():
        feed.tag_button(tagged.id, tag).click()

    expect(feed.search_field).to_have_value("tag")
    expect(feed.search_input).to_have_value(tag)
    expect(feed.card(tagged.id)).to_be_visible()
    expect(feed.card(plain.id)).to_have_count(0)


def test_search_without_matches_offers_to_reset_the_filters(open_as, data, namer):
    feed = PhotoFeedPage(open_as(data.user()))

    feed.search(namer.word("nothing"))

    expect(feed.empty_state).to_contain_text("No photos match your search.")
    feed.empty_reset_button.click()
    expect(feed.search_input).to_have_value("")
    expect(feed.empty_state.filter(has_text="No photos match your search.")).to_have_count(0)


def test_reset_button_restores_the_default_filters(open_as, data, namer):
    feed = PhotoFeedPage(open_as(data.user()))
    expect(feed.reset_button).to_be_disabled()  # nothing to reset yet

    feed.search(namer.word())
    feed.set_min_rating("4")
    expect(feed.reset_button).to_be_enabled()
    feed.reset_button.click()

    expect(feed.search_input).to_have_value("")
    expect(feed.min_rating).to_have_value("")
    expect(feed.reset_button).to_be_disabled()


def test_minimum_rating_filter_keeps_only_well_rated_photos(open_as, data, namer):
    owner, rater, keyword = data.user(), data.user(), namer.word()
    high = data.photo(owner, description=f"high {keyword}")
    low = data.photo(owner, description=f"low {keyword}")
    data.rating(high, rater, 5)
    data.rating(low, rater, 2)
    feed = PhotoFeedPage(open_as(owner))
    feed.search(keyword)
    expect(feed.cards).to_have_count(2)

    feed.set_min_rating("4")

    expect(feed.card(high.id)).to_be_visible()
    expect(feed.card(low.id)).to_have_count(0)
    expect(feed.card_rating(high.id)).to_contain_text("5.0")


def test_sort_by_date_puts_newest_first_and_the_button_reverses_it(open_as, data, namer):
    owner, keyword = data.user(), namer.word()
    start = datetime(2024, 1, 1, 12, 0)
    photos = [data.photo(owner, description=f"{keyword} #{i}", created_at=start + timedelta(hours=i)) for i in range(3)]
    feed = PhotoFeedPage(open_as(owner))

    feed.search(keyword)
    expect(feed.cards.first).to_have_attribute("id", f"photo-card-{photos[2].id}")  # newest first by default

    feed.sort_by("date")  # clicking the active column reverses the direction
    expect(feed.cards.first).to_have_attribute("id", f"photo-card-{photos[0].id}")
    assert feed.card_ids() == [photos[0].id, photos[1].id, photos[2].id]


def test_sort_by_rating_puts_best_rated_first(open_as, data, namer):
    owner, rater, keyword = data.user(), data.user(), namer.word()
    low, best, middle = (data.photo(owner, description=f"{keyword} {n}") for n in ("low", "best", "middle"))
    data.rating(low, rater, 2)
    data.rating(best, rater, 5)
    data.rating(middle, rater, 3)
    feed = PhotoFeedPage(open_as(owner))
    feed.search(keyword)

    feed.sort_by("rating")

    expect(feed.cards.first).to_have_attribute("id", f"photo-card-{best.id}")
    assert feed.card_ids() == [best.id, middle.id, low.id]


def test_second_page_appears_when_there_are_more_than_twenty_photos(open_as, data, namer):
    owner, keyword = data.user(), namer.word()
    data.photos(owner, 21, description=keyword)
    feed = PhotoFeedPage(open_as(owner))

    feed.search(keyword)
    expect(feed.cards).to_have_count(20)
    expect(feed.page_label).to_have_text("Page 1")
    expect(feed.previous_page).to_be_disabled()

    feed.go_next()
    expect(feed.cards).to_have_count(1)
    expect(feed.page_label).to_have_text("Page 2")
    expect(feed.next_page).to_be_disabled()

    feed.go_previous()
    expect(feed.cards).to_have_count(20)


def test_exactly_twenty_photos_lead_to_an_empty_second_page(open_as, data, namer):
    """Known UX quirk: "Next" is enabled whenever a page is full, even if nothing follows."""
    owner, keyword = data.user(), namer.word()
    data.photos(owner, 20, description=keyword)
    feed = PhotoFeedPage(open_as(owner))
    feed.search(keyword)
    expect(feed.cards).to_have_count(20)
    expect(feed.next_page).to_be_enabled()

    feed.go_next()

    expect(feed.empty_state).to_contain_text("There are no more photos.")
    feed.go_previous()
    expect(feed.cards).to_have_count(20)


def test_lightbox_opens_and_closes_with_escape(open_as, data, namer):
    owner, keyword = data.user(), namer.word()
    photo = data.photo(owner, description=keyword)
    page = open_as(owner)
    feed = PhotoFeedPage(page)
    feed.search(keyword)

    feed.zoom(photo.id)
    expect(feed.lightbox).to_be_visible()
    page.keyboard.press("Escape")

    expect(feed.lightbox).to_have_count(0)


def test_lightbox_closes_with_its_button(open_as, data, namer):
    owner, keyword = data.user(), namer.word()
    photo = data.photo(owner, description=keyword)
    feed = PhotoFeedPage(open_as(owner))
    feed.search(keyword)

    feed.zoom(photo.id)
    feed.lightbox_close.click()

    expect(feed.lightbox).to_have_count(0)


def test_opening_a_photo_and_going_back_returns_to_the_feed(open_as, data, namer):
    owner, keyword = data.user(), namer.word()
    photo = data.photo(owner, description=f"detail {keyword}")
    page = open_as(owner)

    view = goto_photo(page, photo, keyword)
    expect(view.heading).to_have_text(f"detail {keyword}")
    view.back_button.click()

    expect(PhotoFeedPage(page).upload_button).to_be_visible()


def test_author_link_opens_the_public_profile(open_as, data, namer):
    owner, viewer, keyword = data.user(), data.user(), namer.word()
    data.photo(owner, description=keyword)
    page = open_as(viewer)
    feed = PhotoFeedPage(page)
    feed.search(keyword)
    photo_id = feed.card_ids()[0]

    feed.open_author(photo_id)

    expect(PublicProfilePage(page).heading).to_have_text(f"@{owner.username}")
