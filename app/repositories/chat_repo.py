import uuid
from time import time

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatMessage, ChatSession
from app.repositories.base import BaseRepository


class ChatSessionRepository(BaseRepository[ChatSession]):

    async def get_by_id_and_user(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ChatSession | None:
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_for_user(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ChatSession], int]:
        count_result = await db.execute(
            select(func.count(ChatSession.id)).where(
                ChatSession.user_id == user_id
            )
        )
        total = count_result.scalar_one()

        result = await db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total


class ChatMessageRepository(BaseRepository[ChatMessage]):

    async def get_session_messages(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        limit: int = 50,
    ) -> list[ChatMessage]:
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_message(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        role: str,
        content: str,
        citations: list | None = None,
        token_count: int = 0,
    ) -> ChatMessage:
        return await self.create(
            db,
            session_id=session_id,
            role=role,
            content=content,
            citations=citations,
            token_count=token_count,
            created_at=time(),
        )


chat_session_repo = ChatSessionRepository(ChatSession)
chat_message_repo = ChatMessageRepository(ChatMessage)