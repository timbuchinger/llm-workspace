from unittest.mock import MagicMock
import pytest
from memory.server import Memory, MemoryTools


# @pytest.fixture
# def mock_vector_store():
#     mock_store = MagicMock()
#     return mock_store
@pytest.fixture
def mock_chroma_collection():
    mock_chroma_collection = MagicMock()
    return mock_chroma_collection


@pytest.fixture
def mock_embeddings():
    mock_embeddings = MagicMock()
    return mock_embeddings


@pytest.fixture
def memory_tools(mock_chroma_collection, mock_embeddings):
    tools = MemoryTools()
    # tools.vector_store = mock_vector_store
    # tools.index = MagicMock()
    # tools.index.vector_store = mock_vector_store
    tools.chroma_collection = mock_chroma_collection
    tools.embedding = mock_embeddings
    return tools


def test_add_memory(memory_tools):
    memory = Memory(content="Test memory", tags=["test"])
    memory_tools.add_memory(memory)
    memory_tools.chroma_collection.insert.assert_called_once()


def test_delete_memory(memory_tools):
    content = "Test memory"
    memory_tools.delete_memory(content)
    memory_tools.chroma_collection.delete.assert_called_once_with(content=content)


def test_search_memory(memory_tools):
    query = "Test query"
    memory_tools.search_memory(query)
    memory_tools.embedding.get_query_embedding.assert_called_once_with(query)
    memory_tools.chroma_collection.query.assert_called_once_with(query, top_k=3)


def test_retrieve_all(memory_tools):
    memory_tools.retrieve_all()
    memory_tools.chroma_collection.get.assert_called_once()


def test_get_by_tag(memory_tools):
    tags = ["test"]
    memory_tools.retrieve_all = MagicMock(
        return_value=[
            {
                "content": "Test memory",
                "metadata": {"tags": ["test"], "date": "2023-01-01T00:00:00"},
            }
        ]
    )
    results = memory_tools.get_by_tag(tags)
    assert len(results) == 1
    assert results[0]["content"] == "Test memory"
