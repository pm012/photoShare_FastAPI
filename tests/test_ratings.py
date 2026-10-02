from src.database.models import Photo

def test_full_ratings_lifecycle_and_constraints(client, db_session):
    # 1. Register 3 users: Admin, Photo owner/author, Evaluator (voter)
    client.post("/api/auth/signup", json={"username": "admin_v", "email": "admin@test.com", "password": "password123"})
    client.post("/api/auth/signup", json={"username": "author_v", "email": "author@test.com", "password": "password123"})
    client.post("/api/auth/signup", json={"username": "voter_v", "email": "voter@test.com", "password": "password123"})

    # Get headers for the login
    def get_token(email):
        res = client.post("/api/auth/login", data={"username": email, "password": "password123"})
        return f"Bearer {res.json()['access_token']}"

    admin_token = get_token("admin@test.com")
    author_token = get_token("author@test.com")
    voter_token = get_token("voter@test.com")

    # 2. Create photo in the test DB using ORM, to avoid 500 error from Cloudinary
    photo = Photo(user_id=2, url="https://fake-url.com", public_id="fake_123", description="Test Photo")
    db_session.add(photo)
    db_session.commit()
    db_session.refresh(photo)

    # 3. Author tries to rate his own photo -> 400 Bad Request
    response = client.post(f"/api/photos/{photo.id}/rate", headers={"Authorization": author_token}, json={"rate": 5})
    assert response.status_code == 400

    # 4. Incorrect rate (6 stars) -> 422 Unprocessable Entity (Pydantic Field валідація)
    response = client.post(f"/api/photos/{photo.id}/rate", headers={"Authorization": voter_token}, json={"rate": 6})
    assert response.status_code == 422

    # 5. Successfull reate (5 stars) from another user
    response = client.post(f"/api/photos/{photo.id}/rate", headers={"Authorization": voter_token}, json={"rate": 5})
    assert response.status_code == 201

    response = client.get(
        f"/api/photos/{photo.id}/ratings",
        headers={"Authorization": admin_token},
    )
    assert response.status_code == 200
    assert response.json()[0]["rate"] == 5
    assert client.get(
        f"/api/photos/{photo.id}/ratings",
        headers={"Authorization": voter_token},
    ).status_code == 403

    # 6. Second rate from the same user -> 400 Bad Request
    response = client.post(f"/api/photos/{photo.id}/rate", headers={"Authorization": voter_token}, json={"rate": 4})
    assert response.status_code == 400

    # 7. Get average rate (Summary)
    response = client.get(f"/api/photos/{photo.id}/rate/summary", headers={"Authorization": voter_token})
    assert response.status_code == 200
    assert response.json()["average_rating"] == 5.0

    # Summary for not existent photo -> 404
    response = client.get("/api/photos/999/rate/summary", headers={"Authorization": voter_token})
    assert response.status_code == 404

    # 8. Admin successfully deletes rate -> 204 No Content
    response = client.delete("/api/photos/rate/1", headers={"Authorization": admin_token})
    assert response.status_code == 204

    # Deletion of not existent rate -> 404
    response = client.delete("/api/photos/rate/999", headers={"Authorization": admin_token})
    assert response.status_code == 404
