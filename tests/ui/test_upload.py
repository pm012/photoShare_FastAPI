import pytest
from playwright.sync_api import expect

from tests.ui.pages.feed_page import PhotoFeedPage

pytestmark = pytest.mark.feed


def test_user_uploads_a_photo_with_description_and_tags(open_as, data, namer, png_file):
    user, keyword = data.user(), namer.word()
    tag_a, tag_b = namer.tag("a"), namer.tag("b")
    data.track_tag(tag_a), data.track_tag(tag_b)
    page = open_as(user)
    feed = PhotoFeedPage(page)

    dialog = feed.open_upload_dialog()
    dialog.choose_file(png_file)
    expect(dialog.preview).to_be_visible()
    dialog.fill(description=f"my upload {keyword}", tags=f"{tag_a}, {tag_b}")
    dialog.submit()
    expect(dialog.dialog).to_have_count(0)

    feed.search(keyword)
    expect(feed.cards).to_have_count(1)
    stored = data.photos_of(user.id)
    assert len(stored) == 1
    assert stored[0]["description"] == f"my upload {keyword}"
    assert stored[0]["tags"] == sorted([tag_a, tag_b])
    assert "/e2e-media/" in stored[0]["url"]  # served by the fake storage, not Cloudinary
    page.wait_for_function("img => img.complete && img.naturalWidth > 0", arg=feed.card_image(stored[0]["id"]).element_handle())


def test_upload_dialog_rejects_files_that_are_not_images(open_as, data, text_file):
    feed = PhotoFeedPage(open_as(data.user()))

    dialog = feed.open_upload_dialog()
    dialog.choose_file(text_file)

    expect(dialog.error).to_have_text("Only JPEG, PNG, or WEBP images are supported.")
    expect(dialog.preview).to_have_count(0)


def test_upload_dialog_blocks_more_than_five_tags(open_as, data, png_file):
    feed = PhotoFeedPage(open_as(data.user()))
    dialog = feed.open_upload_dialog()
    dialog.choose_file(png_file)

    dialog.fill(tags="a, b, c, d, e, f")

    expect(dialog.dialog).to_contain_text("Remove 1 tag(s) to continue")
    expect(dialog.submit_button).to_be_disabled()
    dialog.fill(tags="a, b, c, d, e")
    expect(dialog.submit_button).to_be_enabled()


def test_duplicate_tags_are_counted_once(open_as, data, png_file):
    feed = PhotoFeedPage(open_as(data.user()))
    dialog = feed.open_upload_dialog()
    dialog.choose_file(png_file)

    dialog.fill(tags="a, A, b, B, c, d, e")  # 5 unique tags

    expect(dialog.submit_button).to_be_enabled()
    expect(dialog.dialog).to_contain_text("5/5")


def test_upload_without_a_file_shows_a_hint(open_as, data):
    feed = PhotoFeedPage(open_as(data.user()))
    dialog = feed.open_upload_dialog()

    dialog.submit()

    expect(dialog.error).to_have_text("Please choose an image file.")


def test_backend_rejects_a_text_file_disguised_as_png(open_as, data, fake_png_file):
    feed = PhotoFeedPage(open_as(data.user()))
    dialog = feed.open_upload_dialog()
    dialog.choose_file(fake_png_file)  # the browser sees image/png, only the server can tell the truth

    dialog.submit()

    expect(dialog.error).to_contain_text("not a valid image")
    expect(dialog.dialog).to_be_visible()


def test_selected_file_can_be_removed(open_as, data, png_file):
    feed = PhotoFeedPage(open_as(data.user()))
    dialog = feed.open_upload_dialog()
    dialog.choose_file(png_file)
    expect(dialog.preview).to_be_visible()

    dialog.remove_button.click()

    expect(dialog.preview).to_have_count(0)
    expect(dialog.dropzone).to_be_visible()


def test_upload_dialog_closes_with_cancel_and_with_escape(open_as, data):
    page = open_as(data.user())
    feed = PhotoFeedPage(page)

    dialog = feed.open_upload_dialog()
    dialog.cancel_button.click()
    expect(dialog.dialog).to_have_count(0)

    dialog = feed.open_upload_dialog()
    page.keyboard.press("Escape")
    expect(dialog.dialog).to_have_count(0)
