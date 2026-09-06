from src.database.models import Photo, User, UserRole
from src.repository import comments as repository_comments
from src.repository import photos as repository_photos
from src.repository import users as repository_users
from src.schemas.comments import CommentModel
from src.schemas.photos import PhotoUpdateDescription

# Repository Integration Testing

def create_user(db_session, username, role=UserRole.USER):
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password="hashed",
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_photo_repository_owner_admin_and_search_branches(db_session):
    owner = create_user(db_session, "owner")
    admin = create_user(db_session, "admin", UserRole.ADMIN)
    other = create_user(db_session, "other")

    photo = repository_photos.create_photo(
        owner.id,
        "https://photo",
        "photo-id",
        "Sunset",
        [" Sunset ", ""],
        db_session,
    )
    assert [tag.name for tag in photo.tags] == ["sunset"]

    updated = repository_photos.update_photo_description(
        photo.id, PhotoUpdateDescription(description="Updated"), owner, db_session
    )
    assert updated.description == "Updated"
    assert repository_photos.update_photo_description(
        999, PhotoUpdateDescription(description="Missing"), owner, db_session
    ) is None

    results = repository_photos.search_photos(
        None, " SUNSET ", "rating", "asc", db_session, user_id=owner.id
    )
    assert results[0]["description"] == "Updated"

    repository_photos.delete_photo(photo.id, admin, db_session)
    assert repository_photos.get_photo_by_id(photo.id, db_session) is None
    assert other.id != owner.id


def test_comment_repository_update_delete_and_missing_branches(db_session):
    user = create_user(db_session, "commenter")
    photo = Photo(user_id=user.id, url="https://photo", public_id="photo-id")
    db_session.add(photo)
    db_session.commit()
    db_session.refresh(photo)

    comment = repository_comments.create_comment(
        photo.id, user.id, CommentModel(text="Initial"), db_session
    )
    assert repository_comments.get_comments_by_photo(photo.id, db_session) == [comment]
    assert repository_comments.update_comment(
        comment.id, CommentModel(text="Updated"), db_session
    ).text == "Updated"
    assert repository_comments.update_comment(
        999, CommentModel(text="Missing"), db_session
    ) is None
    assert repository_comments.delete_comment(comment.id, db_session) is not None
    assert repository_comments.delete_comment(999, db_session) is None


def test_user_repository_crud_and_search_branches(db_session):
    user = create_user(db_session, "searchable")
    assert repository_users.get_user_profile_by_username("missing", db_session) is None
    assert repository_users.get_user_profile_by_username("searchable", db_session)[1] == 0
    assert repository_users.update_user_me(999, "missing", db_session) is None
    assert repository_users.ban_user(user.id, False, db_session).is_active is False
    assert repository_users.ban_user(999, True, db_session) is None
    assert repository_users.search_users_admin("search", db_session) == [user]
    assert repository_users.change_user_role(999, UserRole.ADMIN, db_session) is None
    assert repository_users.delete_user(user.id, db_session) is not None
    assert repository_users.delete_user(999, db_session) is None
