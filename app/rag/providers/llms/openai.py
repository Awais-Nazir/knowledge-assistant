from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from app.rag.interfaces import BaseLLM


class OpenAILLM(BaseLLM):

    def __init__(self, model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI()
        self.model = model

    async def generate(
        self,
        prompt: str,
        system: str,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        stream = await self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            stream=True,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta is not None:
                yield delta