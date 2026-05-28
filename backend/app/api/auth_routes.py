from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.user import User
from app.schemas.auth import AuthResponse, UserLoginRequest, UserRegisterRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = AuthService()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegisterRequest, session: AsyncSession = Depends(get_db)) -> AuthResponse:
    return await auth_service.register(payload.email, payload.password, session)


@router.post("/login", response_model=AuthResponse)
async def login(payload: UserLoginRequest, session: AsyncSession = Depends(get_db)) -> AuthResponse:
    return await auth_service.login(payload.email, payload.password, session)


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)) -> dict:
    return {"id": current_user.id, "email": current_user.email, "created_at": current_user.created_at}
