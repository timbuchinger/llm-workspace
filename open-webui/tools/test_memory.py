import os
import pytest
from unittest.mock import MagicMock, patch

from open-webui.tools.memory_v2
import Memory, MemoryTools

@pytest.fixture
def mock_environment(monkeypatch):
  monkeypatch.setenv("CHROMA_URL", "http://mock_chroma_url")
  monkeypatch.setenv("OLLAMA_URL", "http://mock_ollama_url")

@pytest.fixture
def mock_memory_tools(mock_environment):
  with patch("open-webui.tools.memory_v2.OpenAIEmbedding") as MockEmbedding, \
     patch("open-webui.tools.memory_v2.ChromaVectorStore") as MockVectorStore, \
     patch("open-webui.tools.memory_v2.SimpleKeywordTableIndex") as MockIndex:
    mock_embedding = MockEmbedding.return_value
    mock_vector_store = MockVectorStore.return_value
    mock_index = MockIndex.return_value
    tools = MemoryTools()
    tools.index = mock_index
    tools.vector_store = mock_vector_store
    return tools

def test_add_memory(mock_memory_tools):
  memory = Memory("Test memory content", tags=["test"])
  mock_memory_tools.index.insert = MagicMock()
  mock_memory_tools.add_memory(memory)
  mock_memory_tools.index.insert.assert_called_once()

def test_delete_memory(mock_memory_tools):
  content = "Test memory content"
  mock_memory_tools.index.vector_store.delete = MagicMock()
  mock_memory_tools.delete_memory(content)
  mock_memory_tools.index.vector_store.delete.assert_called_once_with(content=content)

def test_search_memory(mock_memory_tools):
  query = "Test query"
  mock_memory_tools.index.query = MagicMock(return_value=[{"content": "result"}])
  results = mock_memory_tools.search_memory(query)
  assert len(results) == 1
  assert results[0]["content"] == "result"
  mock_memory_tools.index.query.assert_called_once_with(query, top_k=3)

def test_retrieve_all(mock_memory_tools):
  mock_memory_tools.index.vector_store.get_all = MagicMock(return_value=[{"content": "memory"}])
  results = mock_memory_tools.retrieve_all()
  assert len(results) == 1
  assert results[0]["content"] == "memory"
  mock_memory_tools.index.vector_store.get_all.assert_called_once()

def test_get_by_tag(mock_memory_tools):
  tags = ["test"]
  mock_memory_tools.retrieve_all = MagicMock(return_value=[
    {"content": "memory1", "metadata": {"tags": ["test"]}},
    {"content": "memory2", "metadata": {"tags": ["example"]}}
  ])
  results = mock_memory_tools.get_by_tag(tags)
  assert len(results) == 1
  assert results[0]["content"] == "memory1"
  mock_memory_tools.retrieve_all.assert_called_once()