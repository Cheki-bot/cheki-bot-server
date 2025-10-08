from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agent.agent import AsyncAgent
from src.agent.schemas import Platform


@pytest.fixture
def mock_chat_model():
    return AsyncMock()


@pytest.fixture
def mock_classify_topic():
    return AsyncMock()


@pytest.fixture
def mock_rag_retrieve():
    return AsyncMock()


@pytest.fixture
def mock_build_topic_prompts():
    return AsyncMock()


@pytest.fixture
def agent(mock_chat_model, mock_classify_topic, mock_rag_retrieve, mock_build_topic_prompts):
    return AsyncAgent(
        chat_model=mock_chat_model,
        classify_topic=mock_classify_topic,
        rag_retrieve=mock_rag_retrieve,
        build_topic_prompts=mock_build_topic_prompts,
    )


@pytest.mark.asyncio
async def test_stream_success(agent, mock_chat_model, mock_classify_topic, mock_rag_retrieve, mock_build_topic_prompts):
    query = "test query"
    mock_classify_topic.return_value = MagicMock(
        topic="test_topic", optimized_query=query, additional_topics=[], description="", user_query=query
    )
    mock_rag_retrieve.return_value = ["doc1", "doc2"]
    mock_build_topic_prompts.return_value = ["prompt1", "prompt2"]

    async def mock_stream(messages):
        for msg in messages:
            yield type("Chunk", (), {"content": msg})()

    mock_chat_model.astream = mock_stream

    result = []
    async for chunk in agent.stream([MagicMock()], platform=Platform.WEB):
        result.append(chunk.content)

    assert len(result) > 0


@pytest.mark.asyncio
async def test_stream_empty_query(
    agent, mock_chat_model, mock_classify_topic, mock_rag_retrieve, mock_build_topic_prompts
):
    query = ""
    mock_classify_topic.return_value = MagicMock(
        topic="test_topic", optimized_query=query, additional_topics=[], description="", user_query=query
    )
    mock_rag_retrieve.return_value = ["doc1"]
    mock_build_topic_prompts.return_value = ["prompt1"]

    async def mock_stream(messages):
        for msg in messages:
            yield type("Chunk", (), {"content": msg})()

    mock_chat_model.astream = mock_stream

    result = []
    async for chunk in agent.stream([MagicMock()], platform=Platform.WEB):
        result.append(chunk.content)

    assert len(result) > 0


@pytest.mark.asyncio
async def test_stream_with_special_characters(
    agent, mock_chat_model, mock_classify_topic, mock_rag_retrieve, mock_build_topic_prompts
):
    query = "test with special chars: !@#$%^&*()"
    mock_classify_topic.return_value = MagicMock(
        topic="test_topic", optimized_query=query, additional_topics=[], description="", user_query=query
    )
    mock_rag_retrieve.return_value = ["doc with special chars: !@#$%^"]
    mock_build_topic_prompts.return_value = ["prompt with special chars: !@#$%^"]

    async def mock_stream(messages):
        for msg in messages:
            yield type("Chunk", (), {"content": msg})()

    mock_chat_model.astream = mock_stream

    result = []
    async for chunk in agent.stream([MagicMock()], platform=Platform.WEB):
        result.append(chunk.content)

    assert len(result) > 0


@pytest.mark.asyncio
async def test_stream_handles_empty_history(
    agent, mock_chat_model, mock_classify_topic, mock_rag_retrieve, mock_build_topic_prompts
):
    query = "test"
    mock_classify_topic.return_value = MagicMock(
        topic="test_topic", optimized_query=query, additional_topics=[], description="", user_query=query
    )
    mock_rag_retrieve.return_value = ["doc"]
    mock_build_topic_prompts.return_value = ["prompt"]

    async def mock_stream(messages):
        for msg in messages:
            yield type("Chunk", (), {"content": msg})()

    mock_chat_model.astream = mock_stream

    result = []
    async for chunk in agent.stream([MagicMock()], platform=Platform.WEB):
        result.append(chunk.content)

    assert len(result) > 0


@pytest.mark.asyncio
async def test_invoke_method(agent, mock_chat_model, mock_classify_topic, mock_rag_retrieve, mock_build_topic_prompts):
    query = "test query"
    mock_classify_topic.return_value = MagicMock(
        topic="test_topic", optimized_query=query, additional_topics=[], description="", user_query=query
    )
    mock_rag_retrieve.return_value = ["doc1", "doc2"]
    mock_build_topic_prompts.return_value = ["prompt1", "prompt2"]

    mock_chat_model.ainvoke.return_value = MagicMock(content="test response")

    result = await agent.invoke([MagicMock()], platform=Platform.WEB)

    assert result == "test response"
