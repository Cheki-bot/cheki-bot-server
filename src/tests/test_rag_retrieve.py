from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.documents import Document
from langchain_mongodb.vectorstores import MongoDBAtlasVectorSearch

from src.agent.commands.rag_retrieve import AsyncRAGRetrieve
from src.agent.schemas import Topic, TopicSelection


@pytest.fixture
def mock_vector_store():
    """Create a mock vector store for testing."""
    return AsyncMock(spec=MongoDBAtlasVectorSearch)


@pytest.fixture
def mock_topic_selection():
    """Create a mock topic selection for testing."""
    return TopicSelection(
        topic=Topic.VERIFICATION_OF_NEWS,
        description="Test topic",
        optimized_query="test query",
        additional_topics=[Topic.CANDIDATES, Topic.ELECTORAL_INFORMATION],
    )


@pytest.fixture
def mock_documents():
    """Create mock documents for testing."""
    return [
        Document(page_content="Document 1 content", metadata={"topic": "test_topic"}),
        Document(page_content="Document 2 content", metadata={"topic": "test_topic"}),
    ]


@pytest.mark.asyncio
class TestAsyncRAGRetrieve:
    """Test cases for AsyncRAGRetrieve class."""

    async def test_init(self, mock_vector_store):
        """Test initialization."""
        rag_retrieve = AsyncRAGRetrieve(mock_vector_store)
        assert rag_retrieve.vec_db == mock_vector_store

    async def test_run_success(self, mock_vector_store, mock_documents):
        """Test successful run with valid inputs."""
        # Mock the vector store's as_retriever method
        mock_retriever = AsyncMock()
        mock_retriever.ainvoke.return_value = mock_documents
        mock_vector_store.as_retriever.return_value = mock_retriever

        rag_retrieve = AsyncRAGRetrieve(mock_vector_store)
        result = await rag_retrieve.run(Topic.VERIFICATION_OF_NEWS, "test query", 5)

        # Verify the call was made correctly
        mock_vector_store.as_retriever.assert_called_once_with(
            search_kwargs={"k": 5, "pre_filter": {"topic": "VERIFICATION_OF_NEWS"}}
        )
        mock_retriever.ainvoke.assert_called_once_with("test query")
        assert result == mock_documents

    async def test_run_with_general_info(self, mock_vector_store, mock_documents):
        """Test run with GENERAL_INFO topic (should not use pre_filter)."""
        # Mock the vector store's as_retriever method
        mock_retriever = AsyncMock()
        mock_retriever.ainvoke.return_value = mock_documents
        mock_vector_store.as_retriever.return_value = mock_retriever

        rag_retrieve = AsyncRAGRetrieve(mock_vector_store)
        result = await rag_retrieve.run(Topic.GENERAL_INFO, "test query", 5)

        # Verify the call was made correctly - no pre_filter for GENERAL_INFO
        mock_vector_store.as_retriever.assert_called_once_with(search_kwargs={"k": 5})
        mock_retriever.ainvoke.assert_called_once_with("test query")
        assert result == mock_documents

    async def test_run_empty_result(self, mock_vector_store):
        """Test run with empty result."""
        # Mock the vector store's as_retriever method
        mock_retriever = AsyncMock()
        mock_retriever.ainvoke.return_value = []

        mock_vector_store.as_retriever.return_value = mock_retriever

        rag_retrieve = AsyncRAGRetrieve(mock_vector_store)
        result = await rag_retrieve.run(Topic.VERIFICATION_OF_NEWS, "test query", 5)

        # Verify the call was made correctly
        mock_vector_store.as_retriever.assert_called_once_with(
            search_kwargs={"k": 5, "pre_filter": {"topic": "VERIFICATION_OF_NEWS"}}
        )
        mock_retriever.ainvoke.assert_called_once_with("test query")
        assert result == []

    async def test_call_method(self, mock_vector_store, mock_documents):
        """Test the __call__ method using the actual call syntax."""
        with patch.object(AsyncRAGRetrieve, "run", return_value=mock_documents):
            rag_retrieve = AsyncRAGRetrieve(mock_vector_store)
            # Using the actual call syntax
            result = await rag_retrieve(Topic.VERIFICATION_OF_NEWS, "test query", 5)

            # Should call the run method
            assert result == mock_documents

    async def test_run_with_exception_handling(self, mock_vector_store):
        """Test run with exception handling."""
        # Mock the vector store's as_retriever method to raise an exception
        mock_retriever = AsyncMock()
        mock_retriever.ainvoke.side_effect = Exception("Retrieval failed")

        mock_vector_store.as_retriever.return_value = mock_retriever

        rag_retrieve = AsyncRAGRetrieve(mock_vector_store)

        # Should handle the exception gracefully
        with pytest.raises(Exception):
            await rag_retrieve.run(Topic.VERIFICATION_OF_NEWS, "test query", 5)
