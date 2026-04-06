from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic CRUD operations shared by every repository.
    Specific repositories inherit this and add their own methods.
    """

    def __init__(self, model: type[ModelType]):
        self.model = model

    async def get_by_id(
        self,
        db: AsyncSession,
        id: UUID,
    ) -> ModelType | None:
        result = await db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        db: AsyncSession,
        **kwargs: Any,
    ) -> ModelType:
        instance = self.model(**kwargs)
        db.add(instance)
        await db.flush()       # writes to DB but doesn't commit yet
        await db.refresh(instance)  # reload to get server defaults
        return instance

    async def delete(
        self,
        db: AsyncSession,
        instance: ModelType,
    ) -> None:
        await db.delete(instance)
        await db.flush()

    async def save(
        self,
        db: AsyncSession,
        instance: ModelType,
    ) -> ModelType:
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance