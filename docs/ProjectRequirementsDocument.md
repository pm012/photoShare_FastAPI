# PhotoShare Application Requirements (REST API)

The core REST API functionality is implemented with **FastAPI**.

---

## Authentication
1. Implement authentication using **JWT tokens**.
2. Users have three roles: **regular user**, **moderator**, and **administrator**. The first user in the system is always an administrator.
3. Different access levels can be implemented with FastAPI dependencies that validate the user's token and role.

---

## Photo Management
1. Users can upload photos with descriptions (`POST`).
2. Users can delete photos (`DELETE`).
3. Users can edit photo descriptions (`PUT`).
4. Users can retrieve a photo through its unique link (`GET`).
5. A photo can have **up to 5 tags**. Tags are optional when uploading a photo.
6. Tags are unique across the application and are submitted by name. If a tag does not exist, it is created; if it does, the existing tag is associated with the photo.
7. Users can apply basic photo operations supported by [Cloudinary Image Transformations](https://cloudinary.com). The application may choose a limited set of Cloudinary transformations.
8. Users can create a URL to a transformed image and a QR code for viewing the photo using the [qrcode](https://pypi.org) library. This is a `POST` operation because a separate link to the transformed image is created and stored in the database.
9. Created links are stored on the server and can be scanned with a mobile phone to view the image.
10. Administrators can perform all **CRUD operations** on users' photos.

---

## Comments
1. Each photo has a comments section. Users can comment on one another's photos.
2. Users can edit their own comments but **cannot delete them**.
3. Administrators and moderators **can delete** comments.
4. Comment creation and edit timestamps must be stored in the database. Comments use a **one-to-many** relationship with photos. Store timestamps in the `created_at` and `updated_at` columns of the comments table.

---

## Additional Functionality
1. Provide a route for a user's public profile, identified by their unique username. Return the user's information, including their name, registration date, number of uploaded photos, and more.
2. Users can view and edit their own information. These must be **separate routes** from the public profile route. Public profiles are available to everyone; the user's own information is editable.
3. Administrators can deactivate (**ban**) users. Inactive users cannot sign in to the application.

### Optional Features (Time Permitting)
1. **Logout:** Implement a logout mechanism. Add the access token to a blacklist for the remainder of its lifetime.
2. **Ratings:**
   * Users can rate a photo from **1 to 5 stars**. The rating is the average of all users' scores.
   * Each user can rate a photo only once.
   * Users cannot rate their own photos.
   * Moderators and administrators can view and delete user ratings.
3. **Search and filtering:**
   * Users can search photos by keyword or tag, then filter results by rating or upload date.
   * Moderators and administrators can search and filter photos by the users who uploaded them.

---

## After Core Functionality
1. Cover the application with unit tests and achieve **more than 90%** test coverage.
2. Deploy the application to a cloud service of your choice. Recommended options: [Koyeb](https://koyeb.com) or [Fly.io](https://fly.io).

---

## Acceptance Criteria
1. The web application is implemented with **FastAPI**.
2. The project is stored in a separate, publicly accessible repository (**GitHub, GitLab, or Bitbucket**).
3. **PostgreSQL** stores users, photos, and comments. Use **SQLAlchemy** (ORM) to interact with the database.
4. The project includes detailed installation and usage instructions.
5. The project fully implements the requirements described in this document.
6. The project provides complete **Swagger** documentation.
7. **Dockerfile:** Create a `Dockerfile` that builds an image for running the application in a container. It must select a base image, copy the code, install dependencies, and define a startup command.
8. **Docker Compose:** Integrate Docker Compose to manage the project. Create a `docker-compose.yml` file describing services, networks, and volumes. It must allow the entire project to be started with one `docker-compose up` command.
