from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass


@dataclass
class RerankedChunk:
    """A retrieved chunk with its reranking score."""

    index: int  # original position in the candidate list
    score: float  # reranker confidence score
    text: str  # chunk content
    metadata: dict  # source info — page number, document name etc


class BaseEmbedder(ABC):
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a list of texts into vectors.
        Returns one vector per input text.
        """
        ...

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        """
        Embed a single query string.
        Separate method because some providers use different
        models for queries vs documents.
        """
        ...


class BaseReranker(ABC):
    @abstractmethod
    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_n: int = 5,
    ) -> list[RerankedChunk]:
        """
        Rerank documents by relevance to query.
        Returns top_n results sorted by score descending.
        """
        ...


class BaseLLM(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: str,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """
        Stream tokens from the LLM.
        Yields token strings as they arrive.
        """
        ...
