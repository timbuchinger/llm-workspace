import asyncio
import json
import os

import mcp_memory.server
import pytest
from dotenv import load_dotenv
from mcp_memory import server
from pymongo import MongoClient
from pytest_lazyfixture import lazy_fixture

load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI")
DATABASE_NAME = "memories"
ENTITIES_COLLECTION = "entities"
RELATIONS_COLLECTION = "relations"

entities = [
    {
        "name": "entity1",
        "entity_type": "tool",
        "observations": ["observation1", "observation2"],
    },
    {"name": "entity2", "entity_type": "person", "observations": []},
    {"name": "entity1", "entity_type": "job", "observations": []},
    {"name": "entity3", "entity_type": "vehicle", "observations": []},
]
# observations = ["observation1", "observation2"]
relations = [
    {"from_entity": "entity1", "to_entity": "entity2", "relation_type": "type1"},
    {"from_entity": "entity2", "to_entity": "entity3", "relation_type": "type2"},
]


@pytest.fixture(scope="function", autouse=True)
def setup_before_each_test():
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    db.entities.drop()
    db.relations.drop()
    db.create_collection(ENTITIES_COLLECTION)
    db.create_collection(RELATIONS_COLLECTION)

    yield

    client.close()


@pytest.fixture(scope="function")
def setup_database():
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    yield db
    client.close()


@pytest.fixture(scope="function")
def setup_manager():
    manager = mcp_memory.server.KnowledgeGraphManager()
    yield manager


@pytest.mark.usefixtures("setup_database")
@pytest.fixture(scope="function")
def setup_entities(setup_manager):
    for entity in entities:
        arguments = dict(
            name=entity["name"],
            entity_type=entity["entity_type"],
            observations=entity["observations"],
        )
        asyncio.run(setup_manager.create_entity(arguments))
    # yield setup_database


@pytest.mark.usefixtures("setup_database", "setup_entities")
@pytest.fixture(scope="function")
def setup_relations(setup_manager):
    for relation in relations:
        arguments = dict(
            from_entity=relation["from_entity"],
            to_entity=relation["to_entity"],
            relation_type=relation["relation_type"],
        )
        asyncio.run(setup_manager.create_relation(arguments))


def test_list_tools():
    tools = asyncio.run(server.list_tools())
    assert len(tools) == 9


def test_create_entity(setup_database):
    name = "create_entity"
    s = """{
            "observations": [
                "observation3",
                "observation4"
            ],
            "entity_type": "tool",
            "name": "entity1"
            }"""
    args = json.loads(s)

    server = mcp_memory.server
    result = asyncio.run(server.handle_call_tool(name, args))
    text = result[0].text
    assert (
        text
        == '{"name": "entity1", "entity_type": "tool", "observations": ["observation3", "observation4"]}'
    )
    # for entity in entities:
    #     arguments = dict(
    #         name=entity["name"],
    #         entity_type=entity["entity_type"],
    #         observations=entity["observations"],
    #     )
    #     asyncio.run(setup_manager.create_entity(arguments))

    assert 1 == setup_database[ENTITIES_COLLECTION].count_documents({})


@pytest.mark.usefixtures("setup_entities")
def test_add_observations(setup_database):
    name = "add_observations"
    s = """{
            "observations": [
                "observation3",
                "observation4"
            ],
            "entity_name": "entity1"
            }"""
    args = json.loads(s)

    server = mcp_memory.server
    result = asyncio.run(server.handle_call_tool(name, args))
    text = result[0].text
    assert (
        text
        == '{"entity_name": "entity1", "added_observations": ["observation3", "observation4"]}'
    )
    # assert result["entity_name"] == entities[0]["name"]
    # assert set(result["added_observations"]) == set(arguments["observations"])
    # TODO: Assert that values in database match the actual values


@pytest.mark.usefixtures("setup_entities")
def test_create_relation(setup_database):
    name = "create_relation"
    s = '{"from_entity": "entity7", "to_entity": "entity8", "relation_type": "type9"}'
    args = json.loads(s)

    server = mcp_memory.server
    result = asyncio.run(server.handle_call_tool(name, args))
    text = result[0].text

    # relations = list(
    #     setup_database[RELATIONS_COLLECTION].find({"from_entity": "entity7"})
    # )

    assert (
        text
        == '{"from_entity": "entity7", "to_entity": "entity8", "relation_type": "type9"}'
    )


@pytest.mark.usefixtures("setup_entities")
def test_delete_entities(setup_database):
    name = "delete_entities"
    s = '{"entity_names": ["entity1"]}'
    args = json.loads(s)

    server = mcp_memory.server
    result = asyncio.run(server.handle_call_tool(name, args))
    text = result[0].text

    assert text == "Entities deleted"
    # arguments = dict(entity_names=[entities[0]["name"]])
    # asyncio.run(setup_manager.delete_entities(arguments))
    # remaining_entities = list(setup_database[ENTITIES_COLLECTION].find())

    # assert entities[0]["name"] not in remaining_entities
    # assert 2 == len(remaining_entities)
    # TODO: Assert that values in database match the actual values


@pytest.mark.usefixtures("setup_entities")
def test_delete_observations(setup_database):
    name = "delete_observations"
    s = '{"entity_name": "entity1", "observations": ["observation1"]}'
    args = json.loads(s)

    server = mcp_memory.server
    result = asyncio.run(server.handle_call_tool(name, args))
    text = result[0].text

    assert text == "Observations deleted"
    # entity_name = entities[0]["name"]
    # observation = entities[0]["observations"][0]

    # arguments = dict(entity_name=entity_name, observations=[observation])
    # asyncio.run(setup_manager.delete_observations(arguments))
    # entity = setup_database[ENTITIES_COLLECTION].find_one({"name": entity_name})
    # assert observation not in entity["observations"]


@pytest.mark.usefixtures("setup_relations")
def test_delete_relation(setup_database):
    # setup_manager = mcp_memory_python.server.KnowledgeGraphManager()

    # arguments = dict(
    #     from_entity=relations[0]["from_entity"],
    #     to_entity=relations[0]["to_entity"],
    #     relation_type=relations[0]["relation_type"],
    # )
    # asyncio.run(setup_manager.delete_relation(arguments))
    name = "delete_relation"
    s = '{"from_entity": "entity1", "to_entity": "entity2", "relation_type": "type1"}'
    args = json.loads(s)

    server = mcp_memory.server
    result = asyncio.run(server.handle_call_tool(name, args))
    text = result[0].text

    assert text == "Relations deleted"

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
    # TODO: Assert that values in database match the actual values


@pytest.mark.usefixtures("setup_entities", "setup_relations")
def test_search_nodes(setup_database):
    # query_string = "entity"
    # arguments = dict(query=query_string)

    # result = asyncio.run(setup_manager.search_nodes(arguments))
    # assert result is not None
    # assert all(query_string in entity["name"] for entity in result.entities)
    name = "search_nodes"
    s = '{"query": "entity"}'
    args = json.loads(s)

    server = mcp_memory.server
    result = asyncio.run(server.handle_call_tool(name, args))
    text = result[0].text
    assert (
        text
        == '{"entities": [{"name": "entity1", "entity_type": "tool", "observations": ["observation1", "observation2"]}, {"name": "entity2", "entity_type": "person", "observations": []}, {"name": "entity3", "entity_type": "vehicle", "observations": []}], "relations": [{"from_entity": "entity1", "to_entity": "entity2", "relation_type": "type1"}, {"from_entity": "entity2", "to_entity": "entity3", "relation_type": "type2"}]}'
    )
    # TODO: Assert that values in database match the actual values


# TODO: Implement this method
# @pytest.mark.usefixtures("setup_database")
# def test_open_nodes(setup_manager):
#     names = ["entity1", "entity2"]

#     result = asyncio.run(setup_manager.open_nodes(names))
#     assert result is not None
#     assert all(entity["name"] in names for entity in result.entities)
#     # TODO: Assert that values in database match the actual values


@pytest.mark.usefixtures("setup_database", "setup_entities", "setup_relations")
def test_read_graph(setup_manager):
    name = "read_graph"

    server = mcp_memory.server
    result = asyncio.run(server.handle_call_tool(name, None))
    text = result[0].text

    assert (
        text
        == '{"entities": [{"name": "entity1", "entity_type": "tool", "observations": ["observation1", "observation2"]}, {"name": "entity2", "entity_type": "person", "observations": []}, {"name": "entity3", "entity_type": "vehicle", "observations": []}], "relations": [{"from_entity": "entity1", "to_entity": "entity2", "relation_type": "type1"}, {"from_entity": "entity2", "to_entity": "entity3", "relation_type": "type2"}]}'
    )
    # graph = asyncio.run(setup_manager.read_graph())
    # assert graph is not None
    # TODO: Assert that values in database match the actual values


# @pytest.mark.usefixtures("setup_entities")
# def test_add_observation_console():
#     server = mcp_memory_python.server
#     name = "add_observations"
#     s = """{
#             "observations": [
#                 "Lives in a cave",
#                 "Likes long walks on the beach"
#             ],
#             "entity_name": "entity1"
#             }"""
#     args = json.loads(s)
#     result = asyncio.run(server.handle_call_tool(name, args))
#     assert result is not None
#     # TODO: Implement a more robust assertion
