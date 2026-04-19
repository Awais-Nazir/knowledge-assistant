import uuid
from dataclasses import dataclass

from rank_bm25 import BM25Okapi
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import DocumentChunk
from app.rag.interfaces import BaseEmbedder


@dataclass
class RetrievedChunk:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    content: str
    metadata: dict
    score: float


async def hybrid_retrieve(
    db: AsyncSession,
    embedder: BaseEmbedder,
    query: str,
    user_id: uuid.UUID,
    top_k: int = 20,
) -> list[RetrievedChunk]:
    """
    Combines dense vector search with sparse BM25 keyword search.
    Fuses results using Reciprocal Rank Fusion (RRF).
    """

    # ── 1. Dense retrieval — vector similarity search ──────
    query_vector = await embedder.embed_query(query)
    vector_str = f"[{','.join(str(x) for x in query_vector)}]"

    # PREVIOUSLY:
    #  vector::vector
    #  NOW:
    #  1 - (embedding <=> CAST(:vector AS vector)) as score

    dense_results = await db.execute(
        text("""
            SELECT id, document_id, content, metadata,
                    1 - (embedding <=> CAST(:vector AS vector)) as score
            FROM document_chunks
            WHERE user_id = :user_id
              AND embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:vector AS vector)
            LIMIT :limit
        """),
        {
            "vector": vector_str,
            "user_id": str(user_id),
            "limit": top_k,
        },
    )
    dense_rows = dense_results.fetchall()

    # ── 2. Sparse retrieval — BM25 keyword search ──────────
    all_chunks_result = await db.execute(
        select(DocumentChunk).where(
            DocumentChunk.user_id == user_id,
            DocumentChunk.embedding.is_not(None),
        )
    )
    all_chunks = list(all_chunks_result.scalars().all())

    sparse_ranked: list[RetrievedChunk] = []
    if all_chunks:
        corpus = [chunk.content.lower().split() for chunk in all_chunks]
        bm25 = BM25Okapi(corpus)
        query_tokens = query.lower().split()
        scores = bm25.get_scores(query_tokens)

        scored = sorted(
            zip(all_chunks, scores),
            key=lambda x: x[1],
            reverse=True,
        )[:top_k]

        sparse_ranked = [
            RetrievedChunk(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                content=chunk.content,
                metadata=chunk.metadata_ or {},
                score=float(score),
            )
            for chunk, score in scored
        ]

    # ── 3. Reciprocal Rank Fusion ──────────────────────────
    dense_ranked = [
        RetrievedChunk(
            chunk_id=row.id,
            document_id=row.document_id,
            content=row.content,
            metadata=row.metadata or {},
            score=float(row.score),
        )
        for row in dense_rows
    ]

    return _rrf_fusion(dense_ranked, sparse_ranked, top_k=top_k)


def _rrf_fusion(
    dense: list[RetrievedChunk],
    sparse: list[RetrievedChunk],
    top_k: int,
    k: int = 60,
) -> list[RetrievedChunk]:
    """
    Reciprocal Rank Fusion — combines two ranked lists into one.

    RRF score = 1/(k + rank_in_list_1) + 1/(k + rank_in_list_2)

    k=60 is the standard constant that prevents high scores from
    dominating. A chunk ranked 1st in both lists scores highest.
    A chunk that only appears in one list gets partial credit.
    """
    scores: dict[uuid.UUID, float] = {}
    chunks: dict[uuid.UUID, RetrievedChunk] = {}

    for rank, chunk in enumerate(dense):
        scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0) + 1 / (k + rank + 1)
        chunks[chunk.chunk_id] = chunk

    for rank, chunk in enumerate(sparse):
        scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0) + 1 / (k + rank + 1)
        chunks[chunk.chunk_id] = chunk

    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    return [chunks[cid] for cid in sorted_ids[:top_k]]
