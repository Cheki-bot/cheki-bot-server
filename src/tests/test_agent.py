from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import HumanMessage

from src.agent.agent import AsyncAgent
from src.agent.schemas import Platform, Topic, TopicSelection


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
def mock_build_topic_context():
    return AsyncMock()


@pytest.fixture
def agent(mock_chat_model, mock_classify_topic, mock_rag_retrieve, mock_build_topic_context):
    return AsyncAgent(
        chat_model=mock_chat_model,
        classify_topic=mock_classify_topic,
        rag_retrieve=mock_rag_retrieve,
        build_topic_context=mock_build_topic_context,
    )


@pytest.mark.asyncio
async def test_stream_success(agent, mock_chat_model, mock_classify_topic, mock_build_topic_context):
    query = "test query"
    topic_selection = TopicSelection(
        topic=Topic.GENERAL_INFO,
        description="User wants general information",
        user_query=query,
        optimized_query=query,
        params={}
    )
    mock_classify_topic.return_value = [topic_selection]
    mock_build_topic_context.return_value = "test context"

    async def mock_stream(messages):
        yield type("Chunk", (), {"content": "test response chunk 1"})()
        yield type("Chunk", (), {"content": "test response chunk 2"})()

    mock_chat_model.astream = mock_stream

    result = []
    async for chunk in agent.stream([HumanMessage(content=query)], platform=Platform.WEB):
        result.append(chunk)

    # Check that we got progress messages and response chunks
    assert len(result) >= 7  # At least 4 progress messages + 2 response chunks + 1 done message
    assert any(chunk.content == "Analizando consulta ..." for chunk in result)
    assert any(chunk.content == "Obteniendo información..." for chunk in result)
    assert any(chunk.content == "Procesando información..." for chunk in result)
    assert any(chunk.content == "Generando respuesta..." for chunk in result)
    assert any(chunk.content == "test response chunk 1" for chunk in result)
    assert any(chunk.content == "test response chunk 2" for chunk in result)
    assert any(chunk.done == True for chunk in result)


@pytest.mark.asyncio
async def test_stream_empty_query(agent, mock_chat_model, mock_classify_topic, mock_build_topic_context):
    query = ""
    topic_selection = TopicSelection(
        topic=Topic.GENERAL_INFO,
        description="User wants general information",
        user_query=query,
        optimized_query=query,
        params={}
    )
    mock_classify_topic.return_value = [topic_selection]
    mock_build_topic_context.return_value = "test context"

    async def mock_stream(messages):
        yield type("Chunk", (), {"content": "response to empty query"})()

    mock_chat_model.astream = mock_stream

    result = []
    async for chunk in agent.stream([HumanMessage(content=query)], platform=Platform.WEB):
        result.append(chunk)

    assert len(result) >= 6  # Progress messages + response chunk + done message
    assert any(chunk.content == "response to empty query" for chunk in result)


@pytest.mark.asyncio
async def test_stream_with_special_characters(agent, mock_chat_model, mock_classify_topic, mock_build_topic_context):
    query = "test with special chars: !@#$%^&*()"
    topic_selection = TopicSelection(
        topic=Topic.GENERAL_INFO,
        description="User query with special characters",
        user_query=query,
        optimized_query=query,
        params={}
    )
    mock_classify_topic.return_value = [topic_selection]
    mock_build_topic_context.return_value = "doc with special chars: !@#$%^"

    async def mock_stream(messages):
        yield type("Chunk", (), {"content": "response with special chars: !@#$%^"})()

    mock_chat_model.astream = mock_stream

    result = []
    async for chunk in agent.stream([HumanMessage(content=query)], platform=Platform.WEB):
        result.append(chunk)

    assert len(result) >= 6  # Progress messages + response chunk + done message
    assert any(chunk.content == "response with special chars: !@#$%^" for chunk in result)


@pytest.mark.asyncio
async def test_stream_handles_empty_history(agent, mock_chat_model, mock_classify_topic, mock_build_topic_context):
    query = "test"
    topic_selection = TopicSelection(
        topic=Topic.GENERAL_INFO,
        description="User wants general information",
        user_query=query,
        optimized_query=query,
        params={}
    )
    mock_classify_topic.return_value = [topic_selection]
    mock_build_topic_context.return_value = "test context"

    async def mock_stream(messages):
        yield type("Chunk", (), {"content": "response to test"})()

    mock_chat_model.astream = mock_stream

    result = []
    async for chunk in agent.stream([HumanMessage(content=query)], platform=Platform.WEB):
        result.append(chunk)

    assert len(result) >= 6  # Progress messages + response chunk + done message
    assert any(chunk.content == "response to test" for chunk in result)


@pytest.mark.asyncio
async def test_invoke_method(agent, mock_chat_model, mock_classify_topic, mock_build_topic_context):
    query = "test query"
    topic_selection = TopicSelection(
        topic=Topic.GENERAL_INFO,
        description="User wants general information",
        user_query=query,
        optimized_query=query,
        params={}
    )
    mock_classify_topic.return_value = [topic_selection]
    mock_build_topic_context.return_value = "test context"

    mock_chat_model.ainvoke.return_value = MagicMock(content="test response")

    result = await agent.invoke([HumanMessage(content=query)], platform=Platform.WEB)

    assert result == "test response"


@pytest.mark.asyncio
async def test_stream_error_handling(agent, mock_chat_model, mock_classify_topic):
    query = "test query"
    mock_classify_topic.side_effect = Exception("Test error")

    result = []
    try:
        async for chunk in agent.stream([HumanMessage(content=query)], platform=Platform.WEB):
            result.append(chunk)
    except Exception:
        pass  # Expected exception, we're testing error handling

    # Should have at least one error chunk
    assert any(chunk.type == "error" for chunk in result)
    assert any("Test error" in chunk.content for chunk in result)
