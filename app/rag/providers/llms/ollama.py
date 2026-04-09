from collections.abc import AsyncGenerator

import httpx

from app.rag.interfaces import BaseLLM


class OllamaLLM(BaseLLM):
    """
    Runs any model locally via Ollama.
    Install Ollama from ollama.ai, then:
      ollama pull llama3.2
    Set LLM_PROVIDER=ollama, LLM_MODEL=llama3.2 in .env
    """

    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = "http://localhost:11434",
    ):
        self.model = model
        self.base_url = base_url

    async def generate(
        self,
        prompt: str,
        system: str,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "stream": True,
                    "options": {"temperature": temperature},
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                },
            ) as response:
                import json
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        token = data.get("message", {}).get("content", "")
                        if token:
                            yield token