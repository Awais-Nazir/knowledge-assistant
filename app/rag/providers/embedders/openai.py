from openai import AsyncOpenAI
from app.rag.interfaces import BaseEmbedder
from app.core.config import settings

class OpenAIEmbedder(BaseEmbedder):

    def __init__(self, model: str = "text-embedding-3-small"):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = await self.client.embeddings.create(
            input=texts,
            model=self.model,
        )
        return [item.embedding for item in response.data]

    async def embed_query(self, text: str) -> list[float]:
        vectors = await self.embed([text])
        return vectors[0]