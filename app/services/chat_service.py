import uuid
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.user import User
from app.rag.pipeline import run_rag_pipeline
from app.repositories.chat_repo import chat_message_repo, chat_session_repo
from app.repositories.memory_repo import memory_repo
from app.schemas.chat import (
    ChatRequest,
    MessageResponse,
    SessionDetailResponse,
    SessionListResponse,
    SessionResponse,
)

# trigger memory summarisation after this many messages
MEMORY_TRIGGER_COUNT = 10


class ChatService:
    async def get_or_create_session(
        self,
        db: AsyncSession,
        user: User,
        session_id: uuid.UUID | None,
    ):
        if session_id:
            session = await chat_session_repo.get_by_id_and_user(
                db, session_id, user.id
            )
            if not session:
                raise NotFoundError("ChatSession", session_id)
            return session

        # create new session
        return await chat_session_repo.create(
            db,
            user_id=user.id,
            title="New conversation",
        )

    async def chat(
        self,
        db: AsyncSession,
        user: User,
        data: ChatRequest,
    ) -> AsyncGenerator[str, None]:
        # get or create session
        session = await self.get_or_create_session(db, user, data.session_id)
        await db.commit()

        # load conversation history
        messages = await chat_message_repo.get_session_messages(db, session.id)
        recent_messages = [
            {"role": m.role, "content": m.content} for m in messages[-6:]
        ]

        # load memory if exists
        memory = await memory_repo.get_by_session(db, session.id)
        memory_summary = memory.summary if memory else None

        # save user message
        await chat_message_repo.create_message(
            db,
            session_id=session.id,
            role="user",
            content=data.message,
        )
        await db.commit()

        # run RAG pipeline — returns async generator
        stream = await run_rag_pipeline(
            db=db,
            query=data.message,
            user_id=user.id,
            memory_summary=memory_summary,
            recent_messages=recent_messages,
        )

        # collect full response while streaming
        full_response = []

        async def _stream_and_save():
            async for token in stream:
                full_response.append(token)
                yield token

            # after streaming completes — save assistant message
            complete_response = "".join(full_response)
            await chat_message_repo.create_message(
                db,
                session_id=session.id,
                role="assistant",
                content=complete_response,
            )

            # update session title from first message
            if len(messages) == 0:
                session.title = data.message[:50]
                await chat_session_repo.save(db, session)

            await db.commit()

            # trigger memory if conversation is long enough
            all_messages = await chat_message_repo.get_session_messages(db, session.id)
            if len(all_messages) >= MEMORY_TRIGGER_COUNT:
                await self._update_memory(db, session.id, user.id, all_messages)
                await db.commit()

        return _stream_and_save()

    async def _update_memory(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        messages: list,
    ) -> None:
        existing = await memory_repo.get_by_session(db, session_id)
        start_from = existing.summarized_up_to if existing else 0
        new_messages = messages[start_from:]

        if not new_messages:
            return

        # build text to summarise
        conversation_text = "\n".join(
            f"{m.role.upper()}: {m.content}" for m in new_messages
        )

        from app.rag.factory import get_llm

        llm = get_llm()

        summary_parts = []
        async for token in llm.generate(
            prompt=conversation_text,
            system=(
                "Summarise this conversation concisely, "
                "preserving all important facts and context. "
                "Be brief but complete."
            ),
            temperature=0.3,
        ):
            summary_parts.append(token)

        new_summary = "".join(summary_parts)

        if existing and existing.summary:
            new_summary = f"{existing.summary}\n\n{new_summary}"

        await memory_repo.create_or_update(
            db,
            session_id=session_id,
            user_id=user_id,
            summary=new_summary,
            summarized_up_to=len(messages),
        )

    async def list_sessions(
        self,
        db: AsyncSession,
        user: User,
        page: int = 1,
        page_size: int = 20,
    ) -> SessionListResponse:
        sessions, total = await chat_session_repo.get_all_for_user(
            db, user.id, page, page_size
        )
        return SessionListResponse(
            items=[SessionResponse.model_validate(s) for s in sessions],
            total=total,
            page=page,
            page_size=page_size,
            has_next=(page * page_size) < total,
            has_previous=page > 1,
        )

    async def get_session_detail(
        self,
        db: AsyncSession,
        user: User,
        session_id: uuid.UUID,
    ) -> SessionDetailResponse:
        session = await chat_session_repo.get_by_id_and_user(db, session_id, user.id)
        if not session:
            raise NotFoundError("ChatSession", session_id)

        messages = await chat_message_repo.get_session_messages(db, session.id)
        return SessionDetailResponse(
            session=SessionResponse.model_validate(session),
            messages=[MessageResponse.model_validate(m) for m in messages],
        )


chat_service = ChatService()
