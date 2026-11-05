"""Collision-free names for test data (safe for parallel workers and repeated runs)."""
import itertools
import os
import uuid


class Namer:
    """Produces e2e_<run>_<worker>_<n> style names.

    * <run>    random per pytest session -> two runs never collide
    * <worker> xdist worker id (gw0, gw1, ...) or "m" -> parallel workers never collide
    * <n>      counter -> names inside one session never collide

    Limits to respect: usernames <= 50 chars, tags <= 30 chars (see models.py).
    """

    def __init__(self) -> None:
        self.run = uuid.uuid4().hex[:6]
        self.worker = os.environ.get("PYTEST_XDIST_WORKER", "m")
        self._counter = itertools.count(1)

    @property
    def prefix(self) -> str:
        """Every name created by this session starts with this (used for the final sweep)."""
        return f"e2e_{self.run}{self.worker}_"

    def _next(self, label: str) -> str:
        return f"e2e_{self.run}{self.worker}_{next(self._counter)}_{label}"[:40]

    def username(self, label: str = "user") -> str:
        return self._next(label)

    def email(self, label: str = "user") -> str:
        # example.com is accepted by email-validator (".test" is rejected).
        return f"{self._next(label)}@example.com"

    def tag(self, label: str = "t") -> str:
        return self._next(label)[:30]

    def word(self, label: str = "kw") -> str:
        """A unique search keyword, e.g. to find only this test's photos in the shared feed."""
        return self._next(label).replace("_", "")
