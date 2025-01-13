import json
import os

import mcp.server.sse
import mcp.types as types
from dotenv import load_dotenv
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI")
DATABASE_NAME = "memories"
ENTITIES_COLLECTION = "entities"
RELATIONS_COLLECTION = "relations"

server = Server("mcp_memory_python")


class Entity:
    def __init__(self, name: str, entity_type: str, observations: list):
        self.name = name
        self.entity_type = entity_type
        self.observations = observations

    def to_dict(self):
        return {
            "name": self.name,
            "entityType": self.entity_type,
            "observations": self.observations,
        }


class Relation:
    def __init__(self, from_entity: str, to_entity: str, relation_type: str):
        self.from_entity = from_entity
        self.to_entity = to_entity
        self.relation_type = relation_type

    def to_dict(self):
        return {
            "from": self.from_entity,
            "to": self.to_entity,
            "relation_type": self.relation_type,
        }


class KnowledgeGraph:
    def __init__(self):
        self.entities = []
        self.relations = []

    def load_from_mongodb(self):
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        entities_collection = db[ENTITIES_COLLECTION]
        relations_collection = db[RELATIONS_COLLECTION]

        self.entities = [
            Entity(entity["name"], entity["entityType"], entity["observations"])
            for entity in entities_collection.find()
        ]
        self.relations = [
            Relation(
                relation["from_entity"],
                relation["to_entity"],
                relation["relation_type"],
            )
            for relation in relations_collection.find()
        ]


class KnowledgeGraphManager:
    async def load_graph(self) -> KnowledgeGraph:
        try:
            graph = KnowledgeGraph()
            graph.load_from_mongodb()
            return graph
        except Exception as e:
            print(f"Error loading graph: {e}")
            return KnowledgeGraph()

    async def readGraph(self) -> KnowledgeGraph:
        return self.loadGraph()

    async def create_entities(self, entities: list[Entity]) -> list[Entity]:
        graph = await self.load_graph()

        new_entities = []
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        entities_collection = db[ENTITIES_COLLECTION]

        for entity in entities:
            if not entities_collection.find_one({"name": entity["name"]}):
                entities_collection.insert_one(entity)
                new_entities.append(entity)

        return new_entities

    async def create_relations(self, relations: list[Relation]) -> list[Relation]:
        graph = await self.load_graph()

        new_relations = []
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        relations_collection = db[RELATIONS_COLLECTION]

        for relation in relations:
            if not relations_collection.find_one(
                {
                    "from_entity": relation["from_entity"],
                    "to_entity": relation["to_entity"],
                    "relation_type": relation["relation_type"],
                }
            ):
                relations_collection.insert_one(relation)
                new_relations.append(relation)

        return new_relations

    async def add_observations(self, entity_name: str, observations: list[str]) -> dict:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        entities_collection = db[ENTITIES_COLLECTION]

        entity = entities_collection.find_one({"name": entity_name})
        if entity:
            new_observations = [
                obs for obs in observations if obs not in entity["observations"]
            ]
            entities_collection.update_one(
                {"name": entity_name},
                {"$set": {"observations": entity["observations"] + new_observations}},
            )
            return {"entity_name": entity_name, "added_observations": new_observations}
        else:
            raise Exception(f"Entity with name {entity_name} not found")

    async def delete_entities(self, entity_names: list[str]) -> None:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        entities_collection = db[ENTITIES_COLLECTION]
        relations_collection = db[RELATIONS_COLLECTION]

        entities_collection.delete_many({"name": {"$in": entity_names}})
        relations_collection.delete_many(
            {
                "$or": [
                    {"from_entity": {"$in": entity_names}},
                    {"to_entity": {"$in": entity_names}},
                ]
            }
        )

    async def delete_observations(
        self, entity_name: str, observations: list[str]
    ) -> None:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        entities_collection = db[ENTITIES_COLLECTION]

        entity = entities_collection.find_one({"name": entity_name})
        if entity:
            # Remove the specified observations from the entity's observations
            updated_observations = [
                observation
                for observation in entity["observations"]
                if observation not in observations
            ]
            entities_collection.update_one(
                {"name": entity_name},
                {"$set": {"observations": updated_observations}},
            )

    async def delete_relations(self, relations: list[Relation]) -> None:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        relations_collection = db[RELATIONS_COLLECTION]

        for relation in relations:
            relations_collection.delete_one(relation)

    async def search_nodes(self, query: str) -> KnowledgeGraph:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        entities_collection = db[ENTITIES_COLLECTION]
        relations_collection = db[RELATIONS_COLLECTION]

        filtered_entities = list(
            entities_collection.find(
                {
                    "$or": [
                        {"name": {"$regex": f".*{query}.*", "$options": "i"}},
                        {"entityType": {"$regex": f".*{query}.*", "$options": "i"}},
                        {"observations": {"$regex": f".*{query}.*", "$options": "i"}},
                    ]
                }
            )
        )

        filtered_entity_names = [entity["name"] for entity in filtered_entities]

        filtered_relations = list(
            relations_collection.find(
                {
                    "$or": [
                        {"from_entity": {"$in": filtered_entity_names}},
                        {"to_entity": {"$in": filtered_entity_names}},
                    ]
                }
            )
        )

        filtered_graph = KnowledgeGraph()
        filtered_graph.entities = filtered_entities
        filtered_graph.relations = filtered_relations

        return filtered_graph

    async def open_nodes(self, names: list[str]) -> KnowledgeGraph:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        entities_collection = db[ENTITIES_COLLECTION]
        relations_collection = db[RELATIONS_COLLECTION]

        filtered_entities = list(entities_collection.find({"name": {"$in": names}}))
        filtered_entity_names = [entity["name"] for entity in filtered_entities]
        filtered_relations = list(
            relations_collection.find(
                {
                    "$or": [
                        {"from_entity": {"$in": filtered_entity_names}},
                        {"to_entity": {"$in": filtered_entity_names}},
                    ]
                }
            )
        )

        filtered_graph = KnowledgeGraph()
        filtered_graph.entities = filtered_entities
        filtered_graph.relations = filtered_relations

        return filtered_graph


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return list_tools_sync()


def list_tools_sync() -> list[types.Tool]:
    return [
        types.Tool(
            name="create_entities",
            description="Create multiple new entities in the knowledge graph",
            inputSchema={
                "type": "object",
                "properties": {
                    "entities": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "The name of the entity",
                                },
                                "entityType": {
                                    "type": "string",
                                    "description": "The type of the entity",
                                },
                                "observations": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "An array of observation contents associated with the entity",
                                },
                            },
                            "required": ["name", "entityType", "observations"],
                        },
                    },
                },
                "required": ["entities"],
            },
        ),
        types.Tool(
            name="create_relations",
            description="Create multiple new relations between entities in the knowledge graph. Relations should be in active voice",
            inputSchema={
                "type": "object",
                "properties": {
                    "relations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "from_entity": {
                                    "type": "string",
                                    "description": "The name of the entity where the relation starts",
                                },
                                "to_entity": {
                                    "type": "string",
                                    "description": "The name of the entity where the relation ends",
                                },
                                "relation_type": {
                                    "type": "string",
                                    "description": "The type of the relation",
                                },
                            },
                            "required": ["from", "to", "relation_type"],
                        },
                    },
                },
                "required": ["relations"],
            },
        ),
        types.Tool(
            name="add_observations",
            description="Add new observations to existing entities in the knowledge graph",
            inputSchema={
                "type": "object",
                "properties": {
                    "observations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "entity_name": {
                                    "type": "string",
                                    "description": "The name of the entity to add the observations to",
                                },
                                "contents": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "An array of observation contents to add",
                                },
                            },
                            "required": ["entity_name", "contents"],
                        },
                    },
                },
                "required": ["observations"],
            },
        ),
        types.Tool(
            name="delete_entities",
            description="Delete multiple entities and their associated relations from the knowledge graph",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "An array of entity names to delete",
                    },
                },
                "required": ["entity_names"],
            },
        ),
        types.Tool(
            name="delete_observations",
            description="Delete specific observations from entities in the knowledge graph",
            inputSchema={
                "type": "object",
                "properties": {
                    "deletions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "entity_name": {
                                    "type": "string",
                                    "description": "The name of the entity containing the observations",
                                },
                                "observations": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "An array of observations to delete",
                                },
                            },
                            "required": ["entity_name", "observations"],
                        },
                    },
                },
                "required": ["deletions"],
            },
        ),
        types.Tool(
            name="delete_relations",
            description="Delete multiple relations from the knowledge graph",
            inputSchema={
                "type": "object",
                "properties": {
                    "relations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "from_entity": {
                                    "type": "string",
                                    "description": "The name of the entity where the relation starts",
                                },
                                "to_entity": {
                                    "type": "string",
                                    "description": "The name of the entity where the relation ends",
                                },
                                "relation_type": {
                                    "type": "string",
                                    "description": "The type of the relation",
                                },
                            },
                            "required": ["from", "to", "relation_type"],
                        },
                        "description": "An array of relations to delete",
                    },
                },
                "required": ["relations"],
            },
        ),
        types.Tool(
            name="read_graph",
            description="Read the entire knowledge graph",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="search_nodes",
            description="Search for nodes in the knowledge graph based on a query",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to match against entity names, types, and observation content",
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="open_nodes",
            description="Open specific nodes in the knowledge graph by their names",
            inputSchema={
                "type": "object",
                "properties": {
                    "names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "An array of entity names to retrieve",
                    },
                },
                "required": ["names"],
            },
        ),
    ]


async def main():
    async with mcp.server.sse.sse_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp_memory_python",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


# if __name__ == "__main__":
#     mcp.run(transport="sse")