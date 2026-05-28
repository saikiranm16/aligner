from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, decode_access_token, hash_password, validate_email, validate_password_strength, verify_password
from app.models.user import User
from app.schemas.auth import AuthResponse, UserResponse


class AuthService:
    """Registration, login, and token-backed user lookup."""

    async def register(self, email: str, password: str, session: AsyncSession) -> AuthResponse:
        normalized_email = validate_email(email)
        validate_password_strength(password)

        existing = await session.execute(select(User).where(User.email == normalized_email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="An account with that email already exists.")

        user = User(email=normalized_email, password_hash=hash_password(password))
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return self._build_auth_response(user)

    async def login(self, email: str, password: str, session: AsyncSession) -> AuthResponse:
        normalized_email = validate_email(email)
        result = await session.execute(select(User).where(User.email == normalized_email))
        user = result.scalar_one_or_none()
        if user is None or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
        return self._build_auth_response(user)

    async def get_user_from_token(self, token: str, session: AsyncSession) -> User:
        payload = decode_access_token(token)
        result = await session.execute(select(User).where(User.id == int(payload["sub"])))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account no longer exists.")
        return user

    @staticmethod
    def _build_auth_response(user: User) -> AuthResponse:
        return AuthResponse(
            access_token=create_access_token(user.id, user.email),
            user=UserResponse(id=user.id, email=user.email, created_at=user.created_at),
        )
