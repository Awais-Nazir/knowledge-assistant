import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import ConversationMemory
from app.repositories.base import BaseRepository


class MemoryRepository(BaseRepository[ConversationMemory]):

    async def get_by_session(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
    ) -> ConversationMemory | None:
        result = await db.execute(
            select(ConversationMemory).where(
                ConversationMemory.session_id == session_id
            )
        )
        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        summary: str,
        summarized_up_to: int,
    ) -> ConversationMemory:
        existing = await self.get_by_session(db, session_id)
        if existing:
            existing.summary = summary
            existing.summarized_up_to = summarized_up_to
            return await self.save(db, existing)
        return await self.create(
            db,
            session_id=session_id,
            user_id=user_id,
            summary=summary,
            summarized_up_to=summarized_up_to,
        )


memory_repo = MemoryRepository(ConversationMemory)