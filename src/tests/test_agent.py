from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.chat_history import BaseChatMessageHistory

from src.core.agent import Agent


@pytest.fixture
def mock_chat_model():
    return AsyncMock()


@pytest.fixture
def mock_context_manager():
    return MagicMock()


@pytest.fixture
def mock_history():
    return MagicMock(spec=BaseChatMessageHistory)


@pytest.fixture
def agent(mock_chat_model, mock_context_manager):
    return Agent(chat_model=mock_chat_model, context_manager=mock_context_manager)


@pytest.mark.asyncio
async def test_stream_success(
    agent, mock_chat_model, mock_context_manager, mock_history
):
    query = "test query"
    mock_messages = ["message1", "message2"]
    mock_context_manager.retrieve_context = AsyncMock(return_value=mock_messages)

    async def mock_stream(messages):
        for msg in messages:
            yield type("Chunk", (), {"content": msg})()

    mock_chat_model.astream = mock_stream

    result = []
    async for chunk in agent.stream(query, mock_history):
        result.append(chunk)

    assert len(result) == 2
    assert result[0] == "message1"
    assert result[1] == "message2"


@pytest.mark.asyncio
async def test_stream_empty_query(
    agent, mock_chat_model, mock_context_manager, mock_history
):
    query = ""
    mock_messages = ["message1"]
    mock_context_manager.retrieve_context = AsyncMock(return_value=mock_messages)

    async def mock_stream(messages):
        for msg in messages:
            yield type("Chunk", (), {"content": msg})()

    mock_chat_model.astream = mock_stream

    result = []
    async for chunk in agent.stream(query, mock_history):
        result.append(chunk)

    assert len(result) == 1
    assert result[0] == "message1"


@pytest.mark.asyncio
async def test_stream_with_special_characters(
    agent, mock_chat_model, mock_context_manager, mock_history
):
    query = "test with special chars: !@#$%^&*()"
    mock_messages = ["message with special chars: !@#$%^"]
    mock_context_manager.retrieve_context = AsyncMock(return_value=mock_messages)

    async def mock_stream(messages):
        for msg in messages:
            yield type("Chunk", (), {"content": msg})()

    mock_chat_model.astream = mock_stream

    result = []
    async for chunk in agent.stream(query, mock_history):
        result.append(chunk)

    assert len(result) == 1
    assert result[0] == "message with special chars: !@#$%^"


@pytest.mark.asyncio
async def test_stream_handles_empty_history(
    agent, mock_chat_model, mock_context_manager
):
    query = "test"
    mock_messages = ["message"]
    mock_context_manager.retrieve_context = AsyncMock(return_value=mock_messages)

    async def mock_stream(messages):
        for msg in messages:
            yield type("Chunk", (), {"content": msg})()

    mock_chat_model.astream = mock_stream

    result = []
    async for chunk in agent.stream(query, None):
        result.append(chunk)

    assert len(result) == 1
    assert result[0] == "message"
