import pytest

from kernel.llms.mock import MockLLM


@pytest.mark.asyncio
async def test_mock_llm_generate():
    llm = MockLLM(response="ok")

    result = await llm.generate("hello")

    assert result == "ok:hello"


@pytest.mark.asyncio
async def test_mock_llm_stream():
    llm = MockLLM(response="ok")

    chunks = []
    async for chunk in llm.stream("hello"):
        chunks.append(chunk)

    assert "".join(chunks) == "ok:hello"
