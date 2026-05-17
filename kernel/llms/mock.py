from collections.abc import AsyncIterator

from kernel.llms.base import BaseLLM


class MockLLM(BaseLLM):
    def __init__(self, response: str = "mock-response") -> None:
        self.response = response

    async def generate(self, prompt: str) -> str:
        return f"{self.response}:{prompt}"

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        for chunk in [self.response, ":", prompt]:
            yield chunk
