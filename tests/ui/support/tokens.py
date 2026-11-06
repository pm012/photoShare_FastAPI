from datetime import datetime, timedelta, timezone

import jwt


def password_reset_token(email: str, secret_key: str, algorithm: str, valid_minutes: int = 30) -> str:
    """Same payload as src/services/email.py::send_reset_password_email."""
    payload = {"sub": email, "scope": "password_reset",
               "exp": datetime.now(timezone.utc) + timedelta(minutes=valid_minutes)}
    return jwt.encode(payload, secret_key, algorithm=algorithm)
