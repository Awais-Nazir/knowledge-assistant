from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import RefreshToken, User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    async def get_by_email(
        self,
        db: AsyncSession,
        email: str,
    ) -> User | None:
        result = await db.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def get_by_id(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    async def create_token(
        self,
        db: AsyncSession,
        user_id: UUID,
        token: str,
        expires_at: datetime,
    ) -> RefreshToken:
        return await self.create(
            db,
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            is_revoked=False,
            created_at=datetime.now(UTC),
        )

    async def get_by_token(
        self,
        db: AsyncSession,
        token: str,
    ) -> RefreshToken | None:
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token == token)
        )
        return result.scalar_one_or_none()

    async def revoke_token(
        self,
        db: AsyncSession,
        token: str,
    ) -> None:
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.token == token)
            .values(is_revoked=True)
        )

    async def revoke_all_for_user(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> None:
        await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False,  # noqa: E712
            )
            .values(is_revoked=True)
        )


# module-level instances — import these, not the classes
user_repo = UserRepository(User)
refresh_token_repo = RefreshTokenRepository(RefreshToken)
