import json
import os
from datetime import datetime

import chromadb
import pytest
from chromadb.config import Settings
from fastapi.testclient import TestClient
from llama_index.embeddings.ollama import OllamaEmbedding
from memory.server import app, tools


@pytest.fixture(scope="function")
def test_client():
    return TestClient(app)


@pytest.fixture(scope="module")
def chroma_client():
    return chromadb.HttpClient(
        settings=Settings(
            anonymized_telemetry=False,
            chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
            chroma_client_auth_credentials=os.environ.get("CHROMA_AUTH_TOKEN"),
        ),
        host=os.environ.get("CHROMA_HOST"),
        port=int(os.environ.get("CHROMA_PORT", 8000)),
        ssl=os.environ.get("CHROMA_USE_SSL", "false").lower() == "true",
    )


@pytest.fixture(autouse=True)
def setup_and_teardown(chroma_client):

    collection_name = "test_memories"
    if collection_name in chroma_client.list_collections():
        chroma_client.delete_collection(collection_name)
    chroma_client.get_or_create_collection(collection_name)

    yield

    pass


@pytest.mark.integration
def test_full_memory_lifecycle(test_client):
    # 1. Add a memory
    memory_data = {
        "content": "Integration test memory",
        "tags": ["test", "integration"],
        "chroma_collection_name": "test_memories",
    }
    response = test_client.post("/add_memory", json=memory_data)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # 2. Search for the memory
    search_data = {
        "query": "integration test",
        "chroma_collection_name": "test_memories",
    }
    response = test_client.post("/search_memory", json=search_data)
    assert response.status_code == 200
    memories = response.json()["memories"]
    assert len(memories) > 0
    assert any("Integration test memory" in str(memory) for memory in memories)

    # 3. Retrieve by tag
    tag_data = {"tags": ["test"], "chroma_collection_name": "test_memories"}
    # tag_data["chroma_collection_name"] = "test"
    response = test_client.post("/get_by_tag", json=tag_data)
    assert response.status_code == 200
    results = response.json()["memories"]
    assert len(results) > 0
    assert "Integration test memory" in str(results)

    # 4. Retrieve all memories
    data = {"chroma_collection_name": "test_memories"}
    response = test_client.post("/retrieve_all", json=data)
    assert response.status_code == 200
    all_memories = response.json()["memories"]
    assert len(all_memories) > 0
    assert "Integration test memory" in str(all_memories)

    # 5. Delete the memory
    response = test_client.request(
        "DELETE",
        "/delete_memory/",
        json={
            "content": "Integration test memory",
            "chroma_collection_name": "test_memories",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"


@pytest.mark.integration
def test_multiple_memories_management(test_client):

    memories = [
        {
            "content": "First test memory",
            "tags": ["test1", "multiple"],
            "chroma_collection_name": "test_memories",
        },
        {
            "content": "Second test memory",
            "tags": ["test2", "multiple"],
            "chroma_collection_name": "test_memories",
        },
        {
            "content": "Third test memory",
            "tags": ["test3", "multiple"],
            "chroma_collection_name": "test_memories",
        },
    ]

    for memory in memories:
        response = test_client.post("/add_memory", json=memory)
        assert response.status_code == 200

    # Test retrieving all memories
    data = {"chroma_collection_name": "test_memories"}
    response = test_client.post("/retrieve_all", json=data)
    assert response.status_code == 200
    all_memories = response.json()["memories"]
    assert len(all_memories) == 3

    # Test tag filtering
    response = test_client.post(
        "/get_by_tag",
        json={"tags": ["multiple"], "chroma_collection_name": "test_memories"},
    )
    assert response.status_code == 200
    tagged_memories = response.json()["memories"]
    assert len(tagged_memories) == 3

    # Test searching with relevance
    search_data = {"query": "Second", "chroma_collection_name": "test_memories"}
    response = test_client.post("/search_memory", json=search_data)
    assert response.status_code == 200
    search_results = response.json()["memories"]
    assert "Second test memory" in str(search_results[0])


@pytest.mark.integration
def test_error_handling(test_client):
    # Test invalid memory (empty content)
    response = test_client.post("/add_memory", json={"content": "", "tags": ["test"]})
    assert response.status_code == 422

    # Test invalid search query
    response = test_client.post("/search_memory", json={"query": ""})
    assert response.status_code == 422

    # Test invalid tags request
    response = test_client.post("/get_by_tag", json={"tags": None})
    assert response.status_code == 422


@pytest.mark.integration
def test_memory_persistence(test_client, chroma_client):
    # Add a memory and verify it's stored in ChromaDB
    memory_data = {
        "content": "Persistence test memory",
        "tags": ["persistence"],
        "chroma_collection_name": "test_memories",
    }

    response = test_client.post("/add_memory", json=memory_data)
    assert response.status_code == 200

    ollama_use_ssl = os.getenv("OLLAMA_USE_SSL", "false").lower() == "true"
    ollama_protocol = "https" if ollama_use_ssl else "http"
    ollama_url = f"{ollama_protocol}://{os.getenv("OLLAMA_HOST")}:{os.getenv('OLLAMA_PORT', 11434)}"

    embedding_function = OllamaEmbedding(
        model_name="nomic-embed-text", base_url=ollama_url
    )
    embedding = embedding_function.get_text_embedding("Persistence test memory")

    # Verify directly in ChromaDBself.chroma_collection.delete(
    collection = chroma_client.get_collection("test_memories")
    results = collection.query(query_embeddings=[embedding], n_results=1)

    assert len(results["documents"]) > 0
    assert "Persistence test memory" in results["documents"][0]
    assert "Persistence test memory" in results["documents"][0]
