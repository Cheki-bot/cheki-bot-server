from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore

from src.agent.commands.rag_retrieve import AsyncRAGRetrieve
from src.agent.schemas import Topic, TopicSelection


@pytest.fixture
def mock_vector_store():
    """Create a mock vector store for testing."""
    return AsyncMock(spec=VectorStore)


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

    async def test_init_with_mongo_engine(self, mock_vector_store):
        """Test initialization with mongo engine."""
        rag_retrieve = AsyncRAGRetrieve(mock_vector_store, db_engine="mongo")
        assert rag_retrieve._AsyncRAGRetrieve__filter_field == "pre_filter"

    async def test_init_without_engine(self, mock_vector_store):
        """Test initialization without engine."""
        rag_retrieve = AsyncRAGRetrieve(mock_vector_store)
        assert rag_retrieve._AsyncRAGRetrieve__filter_field == "filter"

    async def test_init_with_other_engine(self, mock_vector_store):
        """Test initialization with other engine."""
        rag_retrieve = AsyncRAGRetrieve(mock_vector_store, db_engine="postgres")
        assert rag_retrieve._AsyncRAGRetrieve__filter_field == "filter"

    async def test_run_success(self, mock_vector_store, mock_topic_selection):
        """Test successful run with valid inputs."""
        # Create different mock documents for main and additional topics
        main_documents = [
            Document(page_content="Main Document 1", metadata={"topic": "VERIFICATION_OF_NEWS"}),
            Document(page_content="Main Document 2", metadata={"topic": "VERIFICATION_OF_NEWS"}),
            Document(page_content="Main Document 3", metadata={"topic": "VERIFICATION_OF_NEWS"}),
            Document(page_content="Main Document 4", metadata={"topic": "VERIFICATION_OF_NEWS"}),
            Document(page_content="Main Document 5", metadata={"topic": "VERIFICATION_OF_NEWS"}),
        ]

        additional_documents_1 = [
            Document(page_content="Additional 1 Document 1", metadata={"topic": "CANDIDATES"}),
            Document(page_content="Additional 1 Document 2", metadata={"topic": "CANDIDATES"}),
        ]

        additional_documents_2 = [
            Document(page_content="Additional 2 Document 1", metadata={"topic": "ELECTORAL_INFORMATION"}),
            Document(page_content="Additional 2 Document 2", metadata={"topic": "ELECTORAL_INFORMATION"}),
        ]

        # Mock the __retrieve method to return different documents based on the topic
        async def mock_retrieve(topic_name, query, k):
            if topic_name == "VERIFICATION_OF_NEWS" and k == 5:
                return main_documents
            elif topic_name == "CANDIDATES" and k == 2:
                return additional_documents_1
            elif topic_name == "ELECTORAL_INFORMATION" and k == 2:
                return additional_documents_2
            else:
                return []

        with patch.object(AsyncRAGRetrieve, "_AsyncRAGRetrieve__retrieve", side_effect=mock_retrieve):
            rag_retrieve = AsyncRAGRetrieve(mock_vector_store)
            result = await rag_retrieve.run(mock_topic_selection)

            # Verify that we got the correct number of documents
            assert len(result) == 9  # 5 main + 2 additional + 2 additional
            assert result[0].page_content == "Main Document 1"
            assert result[5].page_content == "Additional 1 Document 1"
            assert result[7].page_content == "Additional 2 Document 1"

    async def test_run_empty_additional_topics(self, mock_vector_store, mock_documents):
        """Test run with empty additional topics."""
        # Create topic selection with no additional topics
        topic_selection_no_additional = TopicSelection(
            topic=Topic.VERIFICATION_OF_NEWS,
            description="Test topic",
            optimized_query="test query",
            additional_topics=[],
        )

        with patch.object(AsyncRAGRetrieve, "_AsyncRAGRetrieve__retrieve", return_value=mock_documents):
            rag_retrieve = AsyncRAGRetrieve(mock_vector_store)
            result = await rag_retrieve.run(topic_selection_no_additional)

            # Should return only main documents
            assert len(result) == 2
            assert result[0].page_content == "Document 1 content"

    async def test_run_with_none_additional_topics(self, mock_vector_store, mock_documents):
        """Test run with None additional topics."""
        # Create topic selection with None additional topics (using empty list as default)
        topic_selection_none_additional = TopicSelection(
            topic=Topic.VERIFICATION_OF_NEWS,
            description="Test topic",
            optimized_query="test query",
            additional_topics=[],
        )

        with patch.object(AsyncRAGRetrieve, "_AsyncRAGRetrieve__retrieve", return_value=mock_documents):
            rag_retrieve = AsyncRAGRetrieve(mock_vector_store)
            result = await rag_retrieve.run(topic_selection_none_additional)

            # Should return only main documents
            assert len(result) == 2
            assert result[0].page_content == "Document 1 content"

    async def test_retrieve_success(self, mock_vector_store, mock_documents):
        """Test successful retrieval."""
        # Mock the vector store's as_retriever method
        mock_retriever = AsyncMock()
        mock_retriever.ainvoke.return_value = mock_documents

        mock_vector_store.as_retriever.return_value = mock_retriever

        rag_retrieve = AsyncRAGRetrieve(mock_vector_store)
        result = await rag_retrieve._AsyncRAGRetrieve__retrieve("VERIFICATION_OF_NEWS", "test query", 5)

        # Verify the call was made correctly
        mock_vector_store.as_retriever.assert_called_once_with(
            search_kwargs={"k": 5, "filter": {"topic": "VERIFICATION_OF_NEWS"}}
        )
        mock_retriever.ainvoke.assert_called_once_with("test query")
        assert result == mock_documents

    async def test_retrieve_with_mongo_engine(self, mock_vector_store, mock_documents):
        """Test retrieval with mongo engine."""
        # Mock the vector store's as_retriever method
        mock_retriever = AsyncMock()
        mock_retriever.ainvoke.return_value = mock_documents

        mock_vector_store.as_retriever.return_value = mock_retriever

        rag_retrieve = AsyncRAGRetrieve(mock_vector_store, db_engine="mongo")
        result = await rag_retrieve._AsyncRAGRetrieve__retrieve("VERIFICATION_OF_NEWS", "test query", 5)

        # Verify the call was made correctly with pre_filter
        mock_vector_store.as_retriever.assert_called_once_with(
            search_kwargs={"k": 5, "pre_filter": {"topic": "VERIFICATION_OF_NEWS"}}
        )
        mock_retriever.ainvoke.assert_called_once_with("test query")
        assert result == mock_documents

    async def test_retrieve_empty_result(self, mock_vector_store):
        """Test retrieval with empty result."""
        # Mock the vector store's as_retriever method
        mock_retriever = AsyncMock()
        mock_retriever.ainvoke.return_value = []

        mock_vector_store.as_retriever.return_value = mock_retriever

        rag_retrieve = AsyncRAGRetrieve(mock_vector_store)
        result = await rag_retrieve._AsyncRAGRetrieve__retrieve("VERIFICATION_OF_NEWS", "test query", 5)

        # Verify the call was made correctly
        mock_vector_store.as_retriever.assert_called_once_with(
            search_kwargs={"k": 5, "filter": {"topic": "VERIFICATION_OF_NEWS"}}
        )
        mock_retriever.ainvoke.assert_called_once_with("test query")
        assert result == []

    async def test_run_with_invalid_topic_selection(self, mock_vector_store):
        """Test run with invalid topic selection."""
        # Test with None topic selection
        rag_retrieve = AsyncRAGRetrieve(mock_vector_store)
        with pytest.raises(AttributeError):
            await rag_retrieve.run(None)

    async def test_run_with_missing_topic_attributes(self, mock_vector_store):
        """Test run with topic selection missing attributes."""
        # Create a minimal topic selection with valid structure but missing values
        minimal_selection = TopicSelection(
            topic=Topic.VERIFICATION_OF_NEWS,
            description="Test topic",
            optimized_query="test query",
            additional_topics=[],
        )

        rag_retrieve = AsyncRAGRetrieve(mock_vector_store)
        with patch.object(AsyncRAGRetrieve, "_AsyncRAGRetrieve__retrieve", return_value=[]):
            result = await rag_retrieve.run(minimal_selection)
            assert result == []

    async def test_call_method(self, mock_vector_store, mock_topic_selection, mock_documents):
        """Test the __call__ method."""
        with patch.object(AsyncRAGRetrieve, "run", return_value=mock_documents):
            rag_retrieve = AsyncRAGRetrieve(mock_vector_store)
            result = await rag_retrieve.__call__(mock_topic_selection)

            # Should call the run method
            assert result == mock_documents
