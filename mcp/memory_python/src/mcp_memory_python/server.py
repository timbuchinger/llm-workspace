import json
import logging
import os
import sys

import mcp.server.sse
import mcp.types as types
from dotenv import load_dotenv
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.types import TextContent
from pydantic import BaseModel
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI")
DATABASE_NAME = "memories"
ENTITIES_COLLECTION = "entities"
RELATIONS_COLLECTION = "relations"

server = Server("mcp_memory_python")
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger("mcp_memory_python")


class Entity(BaseModel):
    name: str
    entity_type: str
    observations: list[str]

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data["name"],
            entity_type=data["entity_type"],
            observations=data["observations"],
        )

    def to_dict(self):
        return {
            "name": self.name,
            "entityType": self.entity_type,
            "observations": self.observations,
        }


class Relation(BaseModel):
    from_entity: str
    to_entity: str
    relation_type: str

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            from_entity=data["from_entity"],
            to_entity=data["to_entity"],
            relation_type=data["relation_type"],
        )

    def to_dict(self):
        return {
            "from_entity": self.from_entity,
            "to_entity": self.to_entity,
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
    async def read_graph(self) -> KnowledgeGraph:
        try:
            graph = KnowledgeGraph()
            graph.load_from_mongodb()
            return graph
        except Exception as e:
            print(f"Error loading graph: {e}")
            return KnowledgeGraph()

    async def create_entity(self, arguments) -> list[Entity]:
        # graph = await self.load_graph()
        logger.info("create_entity")
        entity = Entity.from_dict(arguments)
        # entity = Entity.from_dict(arguments)
        logger.info("create_entity2")
        client = MongoClient(MONGO_URI)
        logger.info("create_entity3")
        db = client[DATABASE_NAME]
        logger.info("create_entity4")
        entities_collection = db[ENTITIES_COLLECTION]
        logger.info("create_entity5")
        if not entities_collection.find_one({"name": entity.name}):
            logger.info("inside if")
            entities_collection.insert_one(entity.to_dict())
            logger.info("inside if2")
            return entity
        else:
            return None

        # for entity in entities:
        #     logger.info(f"Name: {entity.name}")
        #     logger.info("inside for")
        #     if not entities_collection.find_one({"name": entity.name}):
        #         logger.info("inside if")
        #         entities_collection.insert_one(entity.to_dict())
        #         new_entities.append(entity)
        # return new_entities

    # async def create_entities(self, entities: list[Entity]) -> list[Entity]:
    #     # graph = await self.load_graph()

    #     new_entities = []
    #     client = MongoClient(MONGO_URI)
    #     db = client[DATABASE_NAME]
    #     entities_collection = db[ENTITIES_COLLECTION]
    #     logger.info("got collection")

    #     for entity in entities:
    #         logger.info(f"Name: {entity.name}")
    #         logger.info("inside for")
    #         if not entities_collection.find_one({"name": entity.name}):
    #             logger.info("inside if")
    #             entities_collection.insert_one(entity.to_dict())
    #             new_entities.append(entity)
    #     return new_entities

    async def create_relations(self, arguments) -> list[Relation]:
        # graph = await self.load_graph()

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

    async def add_observations(self, arguments) -> dict:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        entities_collection = db[ENTITIES_COLLECTION]

        entity = entities_collection.find_one({"name": arguments["entity_name"]})
        if entity:
            new_observations = [
                obs
                for obs in arguments["observations"]
                if obs not in entity["observations"]
            ]
            entities_collection.update_one(
                {"name": arguments["entity_name"]},
                {"$set": {"observations": entity["observations"] + new_observations}},
            )
            return {
                "entity_name": arguments["entity_name"],
                "added_observations": new_observations,
            }
        else:
            raise Exception(f"Entity with name {arguments["entity_name"]} not found")

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


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    """Handle tool operations."""
    logger.info(f"Handling tool {name} with arguments {arguments}")
    if not arguments:
        arguments = {}
    try:
        if name == "create_entity_simple":
            # new_entities = await KnowledgeGraphManager().create_entity(
            #     arguments["name"], arguments["entity_type"], arguments["observations"]
            # )
            new_entities = await KnowledgeGraphManager().create_entity(arguments)
            return [
                TextContent(
                    type="text",
                    text=(entity.to_dict() for entity in new_entities),
                )
            ]
            # logger.info("Creating entity")
            # entity = Entity(
            #     arguments["name"],
            #     arguments["entityType"],
            #     arguments["observations"],
            # )
            # logger.info(f"Entity: {entity}")
            # new_entities = await KnowledgeGraphManager().create_entities([entity])
            # logger.info(f"New entities: {new_entities}")
            # return [
            #     TextContent(
            #         type="text",
            #         text=(entity.to_dict() for entity in new_entities),
            #     )
            # ]
        if name == "create_entities":
            entities_data = json.loads(arguments["entities"])
            print(f"Type of entities_data: {type(entities_data)}")
            print(entities_data)

            logger.info("Creating entities")
            for entity in arguments["entities"]:
                logger.info("Entity: " + str(entity))
                logger.info("Type of entity: " + str(type(entity)))
            entities = [
                Entity(
                    entity["name"],
                    entity["entityType"],
                    entity["observations"],
                )
                for entity in arguments["entities"]
            ]
            logger.info(f"Entities: {entities}")
            new_entities = await KnowledgeGraphManager().create_entities(entities)
            logger.info(f"New entities: {new_entities}")
            return [
                TextContent(
                    type="text",
                    text=(entity.to_dict() for entity in new_entities),
                )
            ]

        elif name == "create_relations":
            relations = [
                Relation(
                    relation["from_entity"],
                    relation["to_entity"],
                    relation["relation_type"],
                )
                for relation in arguments["relations"]
            ]
            new_relations = await KnowledgeGraphManager().create_relations(relations)
            return [
                TextContent(
                    type="text",
                    text=(relation.to_dict() for relation in new_relations),
                )
            ]
        elif name == "add_observations":
            observations = await KnowledgeGraphManager().add_observations(
                arguments["entity_name"], arguments["contents"]
            )
            return [TextContent(type="text", text=json.dumps(observations))]
        elif name == "delete_entities":
            await KnowledgeGraphManager().delete_entities(arguments["entity_names"])
            return [TextContent(type="text", text="Entities deleted")]
        elif name == "delete_observations":
            await KnowledgeGraphManager().delete_observations(
                arguments["entity_name"], arguments["observations"]
            )
            return [TextContent(type="text", text="Observations deleted")]
        elif name == "delete_relations":
            relations = [
                Relation(
                    relation["from_entity"],
                    relation["to_entity"],
                    relation["relation_type"],
                )
                for relation in arguments["relations"]
            ]
            await KnowledgeGraphManager().delete_relations(relations)
            return [TextContent(type="text", text="Relations deleted")]
        elif name == "read_graph":
            graph = await KnowledgeGraphManager().read_graph()
            graph_dict = {
                "entities": [entity.to_dict() for entity in graph.entities],
                "relations": [relation.to_dict() for relation in graph.relations],
            }
            return [TextContent(type="text", text=json.dumps(graph_dict))]
        elif name == "search_nodes":
            graph = await KnowledgeGraphManager().search_nodes(arguments["query"])
            graph_dict = {
                "entities": [entity.to_dict() for entity in graph.entities],
                "relations": [relation.to_dict() for relation in graph.relations],
            }
            return [TextContent(type="text", text=json.dumps(graph_dict))]
        elif name == "open_nodes":
            graph = await KnowledgeGraphManager().open_nodes(arguments["names"])
            graph_dict = {
                "entities": [entity.to_dict() for entity in graph.entities],
                "relations": [relation.to_dict() for relation in graph.relations],
            }
            return [TextContent(type="text", text=json.dumps(graph_dict))]
        else:
            raise Exception(f"Unknown tool name: {name}")

    except Exception as e:
        logger.error(f"Error handling tool {name}: {e}")
        return Exception(f"Error handling tool {name}: {e}")


def list_tools_sync() -> list[types.Tool]:
    return [
        types.Tool(
            name="create_entity_simple",
            description="Create a new entity in the knowledge graph",
            inputSchema=Entity.schema(),
            # inputSchema={
            #     "type": "object",
            #     "properties": {
            #         "name": {
            #             "type": "string",
            #             "description": "The name of the entity",
            #         },
            #         "entityType": {
            #             "type": "string",
            #             "description": "The type of the entity",
            #         },
            #         "observations": {
            #             "type": "array",
            #             "items": {"type": "string"},
            #             "description": "An array of observation contents associated with the entity",
            #         },
            #     },
            #     "required": ["name", "entityType", "observations"],
            # },
        ),
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
    logger.info("Server is starting up")
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        # async with mcp.server.sse.sse_server() as (read_stream, write_stream):
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
