import asyncio
import os

import mcp_memory_python.app
import pytest
from dotenv import load_dotenv
from mcp_memory_python import app
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI")


@pytest.fixture(scope="session", autouse=True)
def setup_before_all_tests():
    # Code to run before all tests
    print("Setup before all tests")
    client = MongoClient(MONGO_URI)
    db = client["memory"]

    # Delete and recreate the collections
    db.entities.drop()
    db.relations.drop()
    db.create_collection("entities")
    db.create_collection("relations")
    yield
    # Code to run after all tests
    print("Teardown after all tests")


@pytest.fixture(scope="function")
def setup_database():
    client = MongoClient(MONGO_URI)
    db = client["memory"]
    yield db
    client.close()


def test_list_tools():
    tools = asyncio.run(app.list_tools())
    assert len(tools) == 9


def test_create_entities(setup_database):
    entities = [
        {"name": "entity1", "type": "tool", "description": "description1"},
        {"name": "entity2", "type": "tool", "description": "description2"},
        {"name": "entity1", "type": "tool", "description": "description3"},
    ]
    manager = mcp_memory_python.app.KnowledgeGraphManager()

    asyncio.run(manager.create_entities(entities))
    assert len(setup_database.collection("entities").find()) == 2
