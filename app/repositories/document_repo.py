import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    async def get_by_id_and_user(
        self,
        db: AsyncSession,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Document | None:
        result = await db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_for_user(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Document], int]:
        # total count
        count_result = await db.execute(
            select(func.count(Document.id)).where(Document.user_id == user_id)
        )
        total = count_result.scalar_one()

        # paginated results
        result = await db.execute(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        documents = list(result.scalars().all())

        return documents, total

    async def update_status(
        self,
        db: AsyncSession,
        document: Document,
        status: DocumentStatus,
        error_message: str | None = None,
        chunk_count: int | None = None,
    ) -> Document:
        document.status = status
        if error_message is not None:
            document.error_message = error_message
        if chunk_count is not None:
            document.chunk_count = chunk_count
        return await self.save(db, document)


document_repo = DocumentRepository(Document)
