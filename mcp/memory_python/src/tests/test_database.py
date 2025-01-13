import asyncio
import os

import mcp_memory_python.app
import pytest
from dotenv import load_dotenv
from mcp_memory_python import app
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI")
DATABASE_NAME = "memories"
ENTITIES_COLLECTION = "entities"
RELATIONS_COLLECTION = "relations"

entities = [
    {"name": "entity1", "type": "tool", "observations": []},
    {"name": "entity2", "type": "tool", "observations": []},
    {"name": "entity1", "type": "tool", "observations": []},
]
observations = ["observation1", "observation2"]
relations = [
    {"from_entity": "entity1", "to_entity": "entity2", "relation_type": "type1"},
    {"from_entity": "entity2", "to_entity": "entity3", "relation_type": "type2"},
]


@pytest.fixture(scope="function", autouse=True)
def setup_before_each_test():
    # Code to run before each test
    print("Setup before each test")
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]

    # Delete and recreate the collections
    db.entities.drop()
    db.relations.drop()
    db.create_collection(ENTITIES_COLLECTION)
    db.create_collection(RELATIONS_COLLECTION)
    yield
    # Code to run after each test
    print("Teardown after each test")
    client.close()


@pytest.fixture(scope="function")
def setup_database():
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    yield db
    client.close()


def test_list_tools():
    tools = asyncio.run(app.list_tools())
    assert len(tools) == 9


def test_create_entities(setup_database):
    manager = mcp_memory_python.app.KnowledgeGraphManager()

    response = asyncio.run(manager.create_entities(entities))
    assert 2 == len(response)

    assert setup_database[ENTITIES_COLLECTION].count_documents({}) == 2


def test_load_from_mongodb(setup_database):
    manager = mcp_memory_python.app.KnowledgeGraphManager()
    graph = asyncio.run(manager.load_graph())
    assert graph is not None


def test_add_observations(setup_database):
    manager = mcp_memory_python.app.KnowledgeGraphManager()

    asyncio.run(manager.create_entities(entities[:2]))
    result = asyncio.run(manager.add_observations(entities[0]["name"], observations))
    assert result["entity_name"] == entities[0]["name"]
    assert set(result["added_observations"]) == set(observations)


def test_delete_entities(setup_database):
    entity_names = ["entity1", "entity2"]
    manager = mcp_memory_python.app.KnowledgeGraphManager()

    asyncio.run(manager.delete_entities(entity_names))
    remaining_entities = list(setup_database[ENTITIES_COLLECTION].find())
    for entity in remaining_entities:
        print(entity)
    assert all(entity["name"] not in entity_names for entity in remaining_entities)


def test_delete_observations(setup_database):
    entity_name = "entity1"
    observations = ["observation1"]
    manager = mcp_memory_python.app.KnowledgeGraphManager()

    asyncio.run(manager.create_entities(entities[:2]))
    asyncio.run(manager.add_observations(entities[0]["name"], observations))
    asyncio.run(manager.delete_observations(entity_name, observations))
    entity = setup_database[ENTITIES_COLLECTION].find_one({"name": entity_name})
    assert all(obs not in entity["observations"] for obs in observations)


def test_delete_relations(setup_database):

    manager = mcp_memory_python.app.KnowledgeGraphManager()

    asyncio.run(manager.create_entities(entities[:2]))
    asyncio.run(manager.create_relations(relations))
    asyncio.run(manager.delete_relations(relations))
    remaining_relations = setup_database[RELATIONS_COLLECTION].find()
    assert all(
        not (
            rel["from_entity"] == r["from_entity"]
            and rel["to_entity"] == r["to_entity"]
            and rel["relation_type"] == r["relation_type"]
        )
        for r in relations
        for rel in remaining_relations
    )


def test_search_nodes(setup_database):
    query = "entity"
    manager = mcp_memory_python.app.KnowledgeGraphManager()

    asyncio.run(manager.create_entities(entities[:2]))
    result = asyncio.run(manager.search_nodes(query))
    assert result is not None
    assert all(query in entity["name"] for entity in result.entities)


def test_open_nodes(setup_database):
    names = ["entity1", "entity2"]
    manager = mcp_memory_python.app.KnowledgeGraphManager()

    asyncio.run(manager.create_entities(entities[:2]))
    result = asyncio.run(manager.open_nodes(names))
    assert result is not None
    assert all(entity["name"] in names for entity in result.entities)
