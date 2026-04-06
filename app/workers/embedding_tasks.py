from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def process_document(self, document_id: str):
    """
    Background task — processes a document into chunks and embeddings.
    We'll implement the full RAG pipeline logic here in feature/rag-pipeline.
    For now it's a placeholder that marks the document as ready.
    """
    import asyncio
    from app.core.config import settings

    async def _process():
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from app.models.document import DocumentStatus
        from app.repositories.document_repo import document_repo
        import uuid

        engine = create_async_engine(settings.DATABASE_URL)
        SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

        async with SessionLocal() as db:
            document = await document_repo.get_by_id(db, uuid.UUID(document_id))
            if not document:
                return

            try:
                await document_repo.update_status(
                    db, document, DocumentStatus.PROCESSING
                )
                await db.commit()

                # ── RAG pipeline goes here (feature/rag-pipeline) ──
                # chunker.chunk(document)
                # embedder.embed(chunks)
                # vector_store.save(chunks)

                await document_repo.update_status(
                    db, document, DocumentStatus.READY, chunk_count=0
                )
                await db.commit()

            except Exception as exc:
                await document_repo.update_status(
                    db, document, DocumentStatus.FAILED,
                    error_message=str(exc)
                )
                await db.commit()
                raise self.retry(exc=exc, countdown=60)

        await engine.dispose()

    asyncio.run(_process())