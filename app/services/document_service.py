import uuid

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    FileTooLargeError,
    NotFoundError,
    UnsupportedFileTypeError,
)
from app.models.document import DocumentStatus
from app.models.user import User
from app.repositories.document_repo import document_repo
from app.schemas.document import DocumentListResponse, DocumentResponse
from app.storage.local import get_storage

ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "text/plain": ".txt",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}


class DocumentService:
    async def upload(
        self,
        db: AsyncSession,
        user: User,
        file: UploadFile,
    ) -> DocumentResponse:
        # validate file type
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise UnsupportedFileTypeError(
                file_type=file.content_type,
                allowed_types=list(ALLOWED_MIME_TYPES.keys()),
            )

        # read file into memory
        file_bytes = await file.read()

        # validate file size
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise FileTooLargeError(max_size_mb=settings.MAX_UPLOAD_SIZE_MB)

        # generate unique storage path
        ext = ALLOWED_MIME_TYPES[file.content_type]
        unique_name = f"{uuid.uuid4()}{ext}"
        storage_path = f"users/{user.id}/documents/{unique_name}"

        # save file to storage
        storage = get_storage()
        await storage.save(file_bytes, storage_path)

        # create document record in database
        document = await document_repo.create(
            db,
            user_id=user.id,
            filename=unique_name,
            original_name=file.filename or unique_name,
            mime_type=file.content_type,
            file_size=len(file_bytes),
            storage_path=storage_path,
            status=DocumentStatus.PENDING,
            chunk_count=0,
        )

        # trigger background processing job
        from app.workers.embedding_tasks import process_document

        process_document.delay(str(document.id))

        return DocumentResponse.model_validate(document)

    async def list_documents(
        self,
        db: AsyncSession,
        user: User,
        page: int = 1,
        page_size: int = 20,
    ) -> DocumentListResponse:
        documents, total = await document_repo.get_all_for_user(
            db, user.id, page, page_size
        )
        return DocumentListResponse(
            items=[DocumentResponse.model_validate(d) for d in documents],
            total=total,
            page=page,
            page_size=page_size,
            has_next=(page * page_size) < total,
            has_previous=page > 1,
        )

    async def delete(
        self,
        db: AsyncSession,
        user: User,
        document_id: uuid.UUID,
    ) -> None:
        document = await document_repo.get_by_id_and_user(db, document_id, user.id)
        if not document:
            raise NotFoundError("Document", document_id)

        # delete from storage
        storage = get_storage()
        await storage.delete(document.storage_path)

        # delete from database (cascades to chunks)
        await document_repo.delete(db, document)


document_service = DocumentService()
