# Роуты регистрации. авторизации, гостевого входа и апдейта
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated

from app.api.v1.schemas.auth import TokenPairResponse, RegisterRequest, LoginRequest, GuestLoginRequest, \
    UpgradeGuestRequest, RefreshRequest
from app.application.services.auth_service import AuthService
from app.core.di import get_auth_service
from app.domain.exceptions import UserAlreadyExistsError, InvalidCredentialsError, UserNotFoundError, InvalidTokenError
from app.api.deps import get_current_user_id

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenPairResponse, status_code=status.HTTP_201_CREATED)
async def register(
        body: RegisterRequest,
        auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> TokenPairResponse:
    try:
        tokens = await auth_service.register(
            email=body.email, password=body.password, display_name=body.display_name
        )
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return TokenPairResponse(access_token=tokens.access_token, refresh_token=tokens.refresh_token)

@router.post("/login", response_model=TokenPairResponse)
async def login(
        body: LoginRequest,
        auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenPairResponse:
    try:
        tokens = await auth_service.login(email=body.email, password=body.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenPairResponse(access_token=tokens.access_token, refresh_token=tokens.refresh_token)

@router.post("/guest", response_model=TokenPairResponse, status_code=status.HTTP_201_CREATED)
async def login_as_guest(
        body: GuestLoginRequest,
        auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenPairResponse:
    tokens = await auth_service.login_as_guest(display_name=body.display_name)
    return TokenPairResponse(access_token=tokens.access_token, refresh_token=tokens.refresh_token)

# Превращает гостя в зарегистированного пользователя
@router.post("/upgrade", response_model=TokenPairResponse)
async def upgrade_guest(
        body: UpgradeGuestRequest,
        user_id: Annotated[str, Depends(get_current_user_id)],
        auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenPairResponse:
    try:
        tokens = await auth_service.upgrade_guest(
            user_id=user_id,
            email=body.email,
            password=body.password)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return TokenPairResponse(access_token=tokens.access_token, refresh_token=tokens.refresh_token)

@router.post("/refresh", response_model=TokenPairResponse)
async def refresh(
        body: RefreshRequest,
        auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenPairResponse:
    try:
        tokens = await auth_service.refresh(body.refresh_token)
    except (InvalidTokenError, UserNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenPairResponse(access_token=tokens.access_token, refresh_token=tokens.refresh_token)