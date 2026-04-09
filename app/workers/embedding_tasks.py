from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def process_document(self, document_id: str):
    import asyncio

    async def _process():
        import uuid
        from sqlalchemy.ext.asyncio import (
            async_sessionmaker,
            create_async_engine,
        )
        from app.core.config import settings
        from app.models.document import DocumentStatus
        from app.repositories.document_repo import document_repo
        from app.repositories.chunk_repo import chunk_repo
        from app.rag.chunker import extract_text_from_file, semantic_chunk
        from app.rag.factory import get_embedder
        from app.storage.local import get_storage

        engine = create_async_engine(settings.DATABASE_URL)
        SessionLocal = async_sessionmaker(
            bind=engine, expire_on_commit=False
        )

        async with SessionLocal() as db:
            document = await document_repo.get_by_id(
                db, uuid.UUID(document_id)
            )
            if not document:
                return

            try:
                # mark as processing
                await document_repo.update_status(
                    db, document, DocumentStatus.PROCESSING
                )
                await db.commit()

                # load file from storage
                storage = get_storage()
                file_path = await storage.get_url(document.storage_path)
                with open(file_path, "rb") as f:
                    file_bytes = f.read()

                # extract text
                text = extract_text_from_file(
                    file_bytes, document.mime_type
                )
                if not text.strip():
                    raise ValueError("No text could be extracted from file")

                # chunk text
                chunks = semantic_chunk(text)

                # embed chunks
                embedder = get_embedder()
                vectors = await embedder.embed(chunks)

                # store chunks in database
                for i, (chunk_text, vector) in enumerate(
                    zip(chunks, vectors)
                ):
                    await chunk_repo.create(
                        db,
                        document_id=document.id,
                        user_id=document.user_id,
                        chunk_index=i,
                        content=chunk_text,
                        embedding=vector,
                        metadata_={
                            "original_name": document.original_name,
                            "chunk_index": i,
                        },
                    )

                await document_repo.update_status(
                    db,
                    document,
                    DocumentStatus.READY,
                    chunk_count=len(chunks),
                )
                await db.commit()

            except Exception as exc:
                await document_repo.update_status(
                    db,
                    document,
                    DocumentStatus.FAILED,
                    error_message=str(exc),
                )
                await db.commit()
                raise self.retry(exc=exc, countdown=60)

        await engine.dispose()

    asyncio.run(_process())