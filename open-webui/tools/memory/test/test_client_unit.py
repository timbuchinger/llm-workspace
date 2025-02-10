from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from memory.client import Tools
from memory.server import Memory, MemoryRequest, QueryRequest, TagsRequest, app

client = TestClient(app)


@pytest.fixture
def tools():
    return Tools()


@pytest.mark.asyncio
@patch("requests.post")
async def test_add_memory_unpack_responses_true(mock_post, tools):
    tools.valves = Tools.Valves(unpack_responses=True)
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"message": "Memory added successfully"}

    result = await tools.add_memory("Test memory", ["tag1", "tag2"])
    assert result == "Memory added successfully"


@pytest.mark.asyncio
@patch("requests.post")
async def test_add_memory_unpack_responses_false(mock_post, tools):
    tools.valves = Tools.Valves(unpack_responses=False)
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"message": "Memory added successfully"}

    result = await tools.add_memory("Test memory", ["tag1", "tag2"])
    assert result == {"message": "Memory added successfully"}


@pytest.mark.asyncio
@patch("requests.delete")
async def test_delete_memory_unpack_responses_true(mock_delete, tools):
    tools.valves = Tools.Valves(unpack_responses=True)
    mock_delete.return_value.status_code = 200
    mock_delete.return_value.json.return_value = {
        "message": "Memory deleted successfully"
    }

    result = await tools.delete_memory("Test memory")
    assert result == "Memory deleted successfully"


@pytest.mark.asyncio
@patch("requests.delete")
async def test_delete_memory_unpack_responses_false(mock_delete, tools):
    tools.valves = Tools.Valves(unpack_responses=False)
    mock_delete.return_value.status_code = 200
    mock_delete.return_value.json.return_value = {
        "message": "Memory deleted successfully"
    }

    result = await tools.delete_memory("Test memory")
    assert result == {"message": "Memory deleted successfully"}


@pytest.mark.asyncio
@patch("requests.post")
async def test_search_memory_unpack_responses_true(mock_post, tools):
    tools.valves = Tools.Valves(unpack_responses=True)
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "memories": [
            {
                "id": 1,
                "content": "Test memory",
                "tags": ["tag1"],
                "date": "2023-01-01T00:00:00Z",
            }
        ]
    }

    result = await tools.search_memory("Test query")
    assert "1: Test memory (tags: ['tag1']) 2023-01-01T00:00:00Z\n" in result


@pytest.mark.asyncio
@patch("requests.post")
async def test_search_memory_unpack_responses_false(mock_post, tools):
    tools.valves = Tools.Valves(unpack_responses=False)
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "memories": [
            {
                "id": 1,
                "content": "Test memory",
                "tags": ["tag1"],
                "date": "2023-01-01T00:00:00Z",
            }
        ]
    }

    result = await tools.search_memory("Test query")
    assert result == {
        "memories": [
            {
                "id": 1,
                "content": "Test memory",
                "tags": ["tag1"],
                "date": "2023-01-01T00:00:00Z",
            }
        ]
    }


@pytest.mark.asyncio
@patch("requests.post")
async def test_retrieve_all_unpack_responses_true(mock_get, tools):
    tools.valves = Tools.Valves(unpack_responses=True)
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "memories": [
            {
                "id": 1,
                "content": "Test memory",
                "tags": ["tag1"],
                "date": "2023-01-01T00:00:00Z",
            }
        ]
    }

    result = await tools.retrieve_all()
    assert "1: Test memory (tags: ['tag1']) 2023-01-01T00:00:00Z\n" in result


@pytest.mark.asyncio
@patch("requests.post")
async def test_retrieve_all_unpack_responses_false(mock_get, tools):
    tools.valves = Tools.Valves(unpack_responses=False)
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "memories": [
            {
                "id": 1,
                "content": "Test memory",
                "tags": ["tag1"],
                "date": "2023-01-01T00:00:00Z",
            }
        ]
    }

    result = await tools.retrieve_all()
    assert result == {
        "memories": [
            {
                "id": 1,
                "content": "Test memory",
                "tags": ["tag1"],
                "date": "2023-01-01T00:00:00Z",
            }
        ]
    }


@pytest.mark.asyncio
@patch("requests.post")
async def test_get_by_tag_unpack_responses_true(mock_post, tools):
    tools.valves = Tools.Valves(unpack_responses=True)
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "memories": [
            {
                "id": 1,
                "content": "Test memory",
                "tags": ["tag1"],
                "date": "2023-01-01T00:00:00Z",
            }
        ]
    }

    result = await tools.get_by_tag(["tag1"])
    assert "1: Test memory (tags: ['tag1']) 2023-01-01T00:00:00Z\n" in result


@pytest.mark.asyncio
@patch("requests.post")
async def test_get_by_tag_unpack_responses_false(mock_post, tools):
    tools.valves = Tools.Valves(unpack_responses=False)
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "memories": [
            {
                "id": 1,
                "content": "Test memory",
                "tags": ["tag1"],
                "date": "2023-01-01T00:00:00Z",
            }
        ]
    }

    result = await tools.get_by_tag(["tag1"])
    assert result == {
        "memories": [
            {
                "id": 1,
                "content": "Test memory",
                "tags": ["tag1"],
                "date": "2023-01-01T00:00:00Z",
            }
        ]
    }


def test_memory_class_initialization():
    # Test default initialization
    memory = Memory(content="test content")
    assert memory.content == "test content"
    assert memory.tags == []
    assert isinstance(memory.date, datetime)

    # Test with custom tags and date
    custom_date = datetime(2024, 1, 1)
    memory = Memory(content="test content", tags=["tag1", "tag2"], date=custom_date)
    assert memory.content == "test content"
    assert memory.tags == ["tag1", "tag2"]
    assert memory.date == custom_date


def test_memory_string_representation():
    memory = Memory(content="This is a long content that should be truncated")
    assert str(memory)[:20] == "Memory(content=This "

    memory = Memory(content="Short content")
    assert "Short content" in str(memory)


def test_pydantic_models():
    # Test MemoryRequest validation
    memory_request = MemoryRequest(
        content="test content", chroma_collection_name="test_memories"
    )
    assert memory_request.content == "test content"
    assert memory_request.tags is None

    memory_request = MemoryRequest(
        content="test content", tags=["tag1"], chroma_collection_name="test_memories"
    )
    assert memory_request.tags == ["tag1"]

    # Test QueryRequest validation
    query_request = QueryRequest(
        query="test query", chroma_collection_name="test_memories"
    )
    assert query_request.query == "test query"

    # Test TagsRequest validation
    tags_request = TagsRequest(
        tags=["tag1", "tag2"], chroma_collection_name="test_memories"
    )
    assert tags_request.tags == ["tag1", "tag2"]


def test_add_memory_without_tags(mock_tools):
    mock_tools.add_memory = MagicMock()
    memory_request = {
        "content": "Test memory",
        "chroma_collection_name": "test_memories",
    }  # No tags provided
    response = client.post("/add_memory", json=memory_request)
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Memory added successfully",
    }


def test_add_memory_empty_content(mock_tools):
    memory_request = {
        "content": "",
        "tags": ["tag1"],
        "chroma_collection_name": "test_memories",
    }
    response = client.post("/add_memory", json=memory_request)
    assert response.status_code == 422  # Validation error


def test_search_memory_empty_query(mock_tools):
    query_request = {"query": ""}
    response = client.post("/search_memory", json=query_request)
    assert response.status_code == 422  # Validation error


def test_get_by_tag_empty_tags(mock_tools):
    tags_request = {"tags": [], "chroma_collection_name": "test_memories"}
    response = client.post("/get_by_tag", json=tags_request)
    assert response.status_code == 200
    mock_tools.get_by_tag.assert_called_once_with([], "test_memories")


@pytest.mark.parametrize(
    "invalid_request",
    [
        {"wrong_field": "test"},
        {},
        {"content": None},
        {"content": 123},  # Non-string content
    ],
)
def test_add_memory_invalid_requests(mock_tools, invalid_request):
    response = client.post("/add_memory", json=invalid_request)
    assert response.status_code == 422  # Validation error


def test_request_logging_middleware():
    with patch("memory.server.logger") as mock_logger:
        memory_request = {"content": "Test memory", "tags": ["tag1"]}
        client.post("/add_memory", json=memory_request)
        mock_logger.info.assert_called()


def test_log_function_call_decorator():
    with patch("memory.server.logger") as mock_logger:
        memory_request = {
            "content": "Test memory",
            "tags": ["tag1"],
            "chroma_collection_name": "test_memories",
        }
        client.post("/add_memory", json=memory_request)
        # Verify both entry and exit logs
        assert mock_logger.info.call_count >= 2
