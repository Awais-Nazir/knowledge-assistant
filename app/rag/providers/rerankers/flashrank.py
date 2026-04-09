import asyncio
from functools import lru_cache

from app.rag.interfaces import BaseReranker, RerankedChunk


@lru_cache(maxsize=1)
def _load_ranker():
    from flashrank import Ranker
    return Ranker()


class FlashRankReranker(BaseReranker):
    """
    Local reranker — no API cost, runs on CPU.
    Uses a small cross-encoder model downloaded once on first use.
    """

    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_n: int = 5,
    ) -> list[RerankedChunk]:
        if not documents:
            return []

        from flashrank import RerankRequest

        ranker = _load_ranker()
        request = RerankRequest(
            query=query,
            passages=[{"text": doc} for doc in documents],
        )

        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: ranker.rerank(request),
        )

        reranked = [
            RerankedChunk(
                index=r["index"],
                score=r["score"],
                text=r["text"],
                metadata={},
            )
            for r in results[:top_n]
        ]

        return reranked