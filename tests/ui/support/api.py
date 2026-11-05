"""Tiny API client used only to obtain login tokens (the UI itself is what tests exercise)."""
from urllib.parse import urlsplit

import httpx


class Api:
    def __init__(self, api_url: str, base_url: str):
        self.api_url = api_url.rstrip("/")
        parts = urlsplit(base_url)
        self.origin = f"{parts.scheme}://{parts.netloc}"

    def token(self, email: str, password: str) -> str:
        response = httpx.post(
            f"{self.api_url}/auth/login",
            data={"username": email, "password": password},  # OAuth2 form: "username" carries the e-mail
            timeout=15,
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def storage_state(self, email: str, password: str) -> dict:
        """Playwright storage state equal to "this user is already logged in"."""
        return {
            "cookies": [],
            "origins": [{"origin": self.origin, "localStorage": [{"name": "token", "value": self.token(email, password)}]}],
        }
