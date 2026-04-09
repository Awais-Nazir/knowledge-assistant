from functools import lru_cache

from app.core.config import settings
from app.rag.interfaces import BaseEmbedder, BaseLLM, BaseReranker


@lru_cache(maxsize=1)
def get_embedder() -> BaseEmbedder:
    match settings.EMBEDDER_PROVIDER:
        case "openai":
            from app.rag.providers.embedders.openai import OpenAIEmbedder
            return OpenAIEmbedder(model=settings.EMBEDDER_MODEL)
        case "huggingface":
            from app.rag.providers.embedders.huggingface import HuggingFaceEmbedder
            return HuggingFaceEmbedder(model=settings.EMBEDDER_MODEL)
        case _:
            raise ValueError(
                f"Unknown embedder provider: {settings.EMBEDDER_PROVIDER}"
            )


@lru_cache(maxsize=1)
def get_llm() -> BaseLLM:
    match settings.LLM_PROVIDER:
        case "openai":
            from app.rag.providers.llms.openai import OpenAILLM
            return OpenAILLM(model=settings.LLM_MODEL)
        case "ollama":
            from app.rag.providers.llms.ollama import OllamaLLM
            return OllamaLLM(
                model=settings.LLM_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
            )
        case _:
            raise ValueError(
                f"Unknown LLM provider: {settings.LLM_PROVIDER}"
            )


@lru_cache(maxsize=1)
def get_reranker() -> BaseReranker:
    match settings.RERANKER_PROVIDER:
        case "flashrank":
            from app.rag.providers.rerankers.flashrank import FlashRankReranker
            return FlashRankReranker()
        case _:
            raise ValueError(
                f"Unknown reranker provider: {settings.RERANKER_PROVIDER}"
            )