import uuid
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.factory import get_embedder, get_llm, get_reranker
from app.rag.hybrid_retriever import RetrievedChunk, hybrid_retrieve
from app.rag.prompt_builder import build_prompt


async def run_rag_pipeline(
    db: AsyncSession,
    query: str,
    user_id: uuid.UUID,
    memory_summary: str | None = None,
    recent_messages: list[dict] | None = None,
) -> AsyncGenerator[str, None]:
    """
    Orchestrates the full RAG pipeline:
    1. Hybrid retrieval (dense + sparse)
    2. Reranking
    3. Prompt building
    4. Streaming LLM generation
    """

    embedder = get_embedder()
    reranker = get_reranker()
    llm = get_llm()

    # ── Stage 1: Hybrid retrieval ──────────────────────────
    candidates = await hybrid_retrieve(
        db=db,
        embedder=embedder,
        query=query,
        user_id=user_id,
        top_k=20,
    )

    if not candidates:
        async def _empty():
            yield "I couldn't find any relevant information in your documents."
        return _empty()

    # ── Stage 2: Reranking ─────────────────────────────────
    reranked = await reranker.rerank(
        query=query,
        documents=[c.content for c in candidates],
        top_n=5,
    )

    # map reranked results back to full chunk objects
    top_chunks: list[RetrievedChunk] = [
        candidates[r.index] for r in reranked
    ]

    # ── Stage 3: Prompt building ───────────────────────────
    system_prompt, user_prompt = build_prompt(
        query=query,
        chunks=top_chunks,
        memory_summary=memory_summary,
        recent_messages=recent_messages,
    )

    # ── Stage 4: Streaming generation ─────────────────────
    return llm.generate(
        prompt=user_prompt,
        system=system_prompt,
    )