from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AlreadyExistsError,
    AuthenticationError,
    NotFoundError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repo import refresh_token_repo, user_repo
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse


class AuthService:

    async def register(
        self,
        db: AsyncSession,
        data: RegisterRequest,
    ) -> UserResponse:
        # check email not already taken
        existing = await user_repo.get_by_email(db, data.email)
        if existing:
            raise AlreadyExistsError(
                resource="User",
                field="email",
                value=data.email,
            )

        # create user
        user = await user_repo.create(
            db,
            email=data.email.lower(),
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role="user",
            is_active=True,
        )

        return UserResponse.model_validate(user)

    async def login(
        self,
        db: AsyncSession,
        data: LoginRequest,
    ) -> TokenResponse:
        # fetch user
        user = await user_repo.get_by_email(db, data.email)
        if not user:
            # same error as wrong password — don't reveal which is wrong
            raise AuthenticationError("Invalid email or password")

        # verify password
        if not verify_password(data.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        # check account is active
        if not user.is_active:
            raise AuthenticationError("Account is disabled")

        # create tokens
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))

        # store refresh token in database
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=7
        )
        await refresh_token_repo.create_token(
            db,
            user_id=user.id,
            token=refresh_token,
            expires_at=expires_at,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh(
        self,
        db: AsyncSession,
        data: RefreshRequest,
    ) -> AccessTokenResponse:
        # decode and validate refresh token
        payload = decode_token(data.refresh_token, expected_type="refresh")
        user_id = payload.get("sub")

        # check token exists in database and is not revoked
        token_record = await refresh_token_repo.get_by_token(
            db, data.refresh_token
        )
        if not token_record or token_record.is_revoked:
            raise AuthenticationError("Invalid or revoked refresh token")

        # check token not expired
        if token_record.expires_at < datetime.now(timezone.utc):
            raise AuthenticationError("Refresh token expired")

        # fetch user
        user = await user_repo.get_by_id(db, token_record.user_id)
        if not user or not user.is_active:
            raise AuthenticationError("User not found or disabled")

        # issue new access token
        access_token = create_access_token(subject=str(user.id))

        return AccessTokenResponse(access_token=access_token)

    async def logout(
        self,
        db: AsyncSession,
        refresh_token: str,
    ) -> None:
        await refresh_token_repo.revoke_token(db, refresh_token)

    async def logout_all(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> None:
        from uuid import UUID
        await refresh_token_repo.revoke_all_for_user(
            db, UUID(user_id)
        )


auth_service = AuthService()