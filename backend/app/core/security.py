from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status

from app.core.config import get_settings


def hash_password(password: str) -> str:
    """Hash passwords with PBKDF2 so we avoid storing raw secrets."""

    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"{base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(derived).decode()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_encoded, hash_encoded = stored_hash.split("$", 1)
        salt = base64.urlsafe_b64decode(salt_encoded.encode())
        expected = base64.urlsafe_b64decode(hash_encoded.encode())
    except ValueError:
        return False

    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return hmac.compare_digest(candidate, expected)


def create_access_token(user_id: int, email: str) -> str:
    """Create a signed bearer token without introducing a JWT dependency."""

    settings = get_settings()
    payload = {
        "sub": user_id,
        "email": email,
        "exp": int((datetime.now(UTC) + timedelta(minutes=settings.auth_token_expiry_minutes)).timestamp()),
        "nonce": secrets.token_hex(8),
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")
    signature = hmac.new(settings.auth_secret_key.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")
    return f"{payload_b64}.{signature_b64}"


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        payload_b64, signature_b64 = token.split(".", 1)
    except ValueError as exc:
        raise _unauthorized("Invalid token format.") from exc

    expected_sig = hmac.new(settings.auth_secret_key.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).digest()
    provided_sig = _urlsafe_b64decode(signature_b64)
    if not hmac.compare_digest(expected_sig, provided_sig):
        raise _unauthorized("Invalid token signature.")

    payload = json.loads(_urlsafe_b64decode(payload_b64).decode("utf-8"))
    if int(payload.get("exp", 0)) < int(datetime.now(UTC).timestamp()):
        raise _unauthorized("Token has expired.")
    return payload


def validate_password_strength(password: str) -> None:
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")
    if password.lower() == password or password.upper() == password:
        raise HTTPException(status_code=400, detail="Password must mix uppercase and lowercase characters.")
    if not any(character.isdigit() for character in password):
        raise HTTPException(status_code=400, detail="Password must include at least one number.")


def validate_email(email: str) -> str:
    normalized = email.strip().lower()
    if "@" not in normalized or "." not in normalized.split("@")[-1]:
        raise HTTPException(status_code=400, detail="Enter a valid email address.")
    return normalized


def _urlsafe_b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("utf-8"))


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

