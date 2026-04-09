import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chunk import DocumentChunk
from app.repositories.base import BaseRepository


class ChunkRepository(BaseRepository[DocumentChunk]):

    async def create(
        self,
        db: AsyncSession,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
        chunk_index: int,
        content: str,
        embedding: list[float],
        metadata_: dict,
    ) -> DocumentChunk:
        return await super().create(
            db,
            document_id=document_id,
            user_id=user_id,
            chunk_index=chunk_index,
            content=content,
            embedding=embedding,
            metadata_=metadata_,
        )


chunk_repo = ChunkRepository(DocumentChunk)