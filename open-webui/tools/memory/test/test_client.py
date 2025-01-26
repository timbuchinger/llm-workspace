from unittest.mock import patch

import pytest
from memory.client import Tools


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
                "timestamp": "2023-01-01T00:00:00Z",
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
                "timestamp": "2023-01-01T00:00:00Z",
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
                "timestamp": "2023-01-01T00:00:00Z",
            }
        ]
    }


@pytest.mark.asyncio
@patch("requests.get")
async def test_retrieve_all_unpack_responses_true(mock_get, tools):
    tools.valves = Tools.Valves(unpack_responses=True)
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "memories": [
            {
                "id": 1,
                "content": "Test memory",
                "tags": ["tag1"],
                "timestamp": "2023-01-01T00:00:00Z",
            }
        ]
    }

    result = await tools.retrieve_all()
    assert "1: Test memory (tags: ['tag1']) 2023-01-01T00:00:00Z\n" in result


@pytest.mark.asyncio
@patch("requests.get")
async def test_retrieve_all_unpack_responses_false(mock_get, tools):
    tools.valves = Tools.Valves(unpack_responses=False)
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "memories": [
            {
                "id": 1,
                "content": "Test memory",
                "tags": ["tag1"],
                "timestamp": "2023-01-01T00:00:00Z",
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
                "timestamp": "2023-01-01T00:00:00Z",
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
                "timestamp": "2023-01-01T00:00:00Z",
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
                "timestamp": "2023-01-01T00:00:00Z",
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
                "timestamp": "2023-01-01T00:00:00Z",
            }
        ]
    }
