import asyncio
from functools import lru_cache

from app.rag.interfaces import BaseEmbedder


@lru_cache(maxsize=1)
def _load_model(model_name: str):
    """
    Load model once and cache it.
    lru_cache ensures we don't reload on every request.
    Loading a SentenceTransformer model takes 2-5 seconds.
    """
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


class HuggingFaceEmbedder(BaseEmbedder):
    def __init__(self, model: str = "BAAI/bge-small-en-v1.5"):
        self.model_name = model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        model = _load_model(self.model_name)
        # run in thread pool — SentenceTransformer is synchronous
        loop = asyncio.get_event_loop()
        vectors = await loop.run_in_executor(
            None, lambda: model.encode(texts, normalize_embeddings=True).tolist()
        )
        return vectors

    async def embed_query(self, text: str) -> list[float]:
        # BGE models work better with this prefix for queries
        query_text = f"Represent this sentence for searching: {text}"
        vectors = await self.embed([query_text])
        return vectors[0]
