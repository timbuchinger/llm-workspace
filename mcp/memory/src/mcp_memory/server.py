import json
import logging
import os
import sys
from typing import Annotated

import anyio
import mcp.server.stdio
import mcp.types as types
from dotenv import load_dotenv
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.sse import SseServerTransport
from mcp.shared.exceptions import McpError
from mcp.types import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    ErrorData,
    GetPromptResult,
    Prompt,
    PromptArgument,
    PromptMessage,
    TextContent,
    Tool,
)
from pydantic import BaseModel, Field
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI")
DATABASE_NAME = "memories"
ENTITIES_COLLECTION = "entities"
RELATIONS_COLLECTION = "relations"

server = Server("mcp_memory")
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger("mcp_memory")


class Entity(BaseModel):
    """
    A class used to represent an Entity.

    Methods
        from_dict(cls, data: dict) -> 'Entity'
            Creates an instance of Entity from a dictionary.
        to_dict(self) -> dict
            Converts the Entity instance to a dictionary.
    """

    name: Annotated[
        str,
        Field(
            description="The name of the entity.",
        ),
    ]
    entity_type: Annotated[
        str,
        Field(
            description="The type of the entity.",
        ),
    ]
    observations: Annotated[
        list[str],
        Field(
            description="A list of observations related to the entity.",
        ),
    ]

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
            "entity_type": self.entity_type,
            "observations": self.observations,
        }


class Relation(BaseModel):
    """
    Represents a relationship between two entities.

    Methods:
        from_dict(data: dict) -> Relation:
            Creates an instance of Relation from a dictionary.
        to_dict() -> dict:
            Converts the Relation instance to a dictionary.
    """

    from_entity: Annotated[
        str,
        Field(
            description="The entity from which the relation originates.",
        ),
    ]
    to_entity: Annotated[
        str,
        Field(
            description="The entity to which the relation points.",
        ),
    ]
    relation_type: Annotated[
        str,
        Field(
            description="The type of the relation.",
        ),
    ]

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


class KnowledgeGraph(BaseModel):
    entities: list[Entity]
    relations: list[Relation]

    # def load_from_mongodb(self):
    #     client = MongoClient(MONGO_URI)
    #     db = client[DATABASE_NAME]
    #     entities_collection = db[ENTITIES_COLLECTION]
    #     relations_collection = db[RELATIONS_COLLECTION]
    #     self.entities = [
    #         Entity.from_dict(
    #             dict(
    #                 name=entity["name"],
    #                 entity_type=entity["entity_type"],
    #                 observations=entity["observations"],
    #             )
    #         )
    #         for entity in entities_collection.find()
    #     ]
    #     self.relations = [
    #         Relation.from_dict(
    #             dict(
    #                 from_entity=relation["from_entity"],
    #                 to_entity=relation["to_entity"],
    #                 relation_type=relation["relation_type"],
    #             )
    #         )
    #         for relation in relations_collection.find()
    #     ]

    def to_dict(self):
        return {"entities": self.entities, "relations": self.relations}


class KnowledgeGraphManager:
    async def read_graph(self) -> KnowledgeGraph:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        entities = db[ENTITIES_COLLECTION].find()
        relations = db[RELATIONS_COLLECTION].find()
        graph = KnowledgeGraph(entities=entities, relations=relations)
        return graph

    async def create_entity(self, arguments: dict) -> list[Entity]:
        entity = Entity.from_dict(arguments)
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        entities_collection = db[ENTITIES_COLLECTION]
        if not entities_collection.find_one({"name": entity.name}):
            entities_collection.insert_one(entity.to_dict())
            return entity
        else:
            return None

    async def create_relation(self, arguments: dict) -> list[Relation]:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        relations_collection = db[RELATIONS_COLLECTION]

        if not relations_collection.find_one(
            {
                "from_entity": arguments["from_entity"],
                "to_entity": arguments["to_entity"],
                "relation_type": arguments["relation_type"],
            }
        ):
            relation = Relation.from_dict(arguments)
            relations_collection.insert_one(relation.to_dict())
            return relation

        return None

    async def add_observations(self, arguments: dict) -> dict:
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

    async def delete_entities(self, arguments: dict) -> None:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        entities_collection = db[ENTITIES_COLLECTION]
        relations_collection = db[RELATIONS_COLLECTION]

        entity_names = arguments["entity_names"]

        entities_collection.delete_many({"name": {"$in": entity_names}})
        relations_collection.delete_many(
            {
                "$or": [
                    {"from_entity": {"$in": entity_names}},
                    {"to_entity": {"$in": entity_names}},
                ]
            }
        )

    async def delete_observations(self, arguments: dict) -> None:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        entities_collection = db[ENTITIES_COLLECTION]

        entity_name = arguments["entity_name"]
        observations = arguments["observations"]

        entity = entities_collection.find_one({"name": entity_name})
        if entity:
            updated_observations = [
                observation
                for observation in entity["observations"]
                if observation not in observations
            ]
            entities_collection.update_one(
                {"name": entity_name},
                {"$set": {"observations": updated_observations}},
            )

    async def delete_relation(self, arguments: dict) -> None:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        relations_collection = db[RELATIONS_COLLECTION]

        relation = Relation.from_dict(arguments)

        relations_collection.delete_one(relation.to_dict())

    async def search_nodes(self, arguments: dict) -> KnowledgeGraph:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        entities_collection = db[ENTITIES_COLLECTION]
        relations_collection = db[RELATIONS_COLLECTION]

        query = arguments["query"]

        filtered_entities = list(
            entities_collection.find(
                {
                    "$or": [
                        {"name": {"$regex": f".*{query}.*", "$options": "i"}},
                        {"entity_type": {"$regex": f".*{query}.*", "$options": "i"}},
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

        filtered_graph = KnowledgeGraph(
            entities=filtered_entities, relations=filtered_relations
        )

        return filtered_graph

    # TODO: Implement this method
    # async def open_nodes(self, entity_names: list[str]) -> KnowledgeGraph:
    #     client = MongoClient(MONGO_URI)
    #     db = client[DATABASE_NAME]
    #     entities_collection = db[ENTITIES_COLLECTION]
    #     relations_collection = db[RELATIONS_COLLECTION]

    #     filtered_entities = list(
    #         entities_collection.find({"name": {"$in": entity_names}})
    #     )
    #     filtered_entity_names = [entity["name"] for entity in filtered_entities]
    #     filtered_relations = list(
    #         relations_collection.find(
    #             {
    #                 "$or": [
    #                     {"from_entity": {"$in": filtered_entity_names}},
    #                     {"to_entity": {"$in": filtered_entity_names}},
    #                 ]
    #             }
    #         )
    #     )

    #     filtered_graph = KnowledgeGraph()
    #     filtered_graph.entities = filtered_entities
    #     filtered_graph.relations = filtered_relations

    #     return filtered_graph


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
        if name == "create_entity":
            new_entity = await KnowledgeGraphManager().create_entity(arguments)
            return [
                TextContent(
                    type="text",
                    text=json.dumps(new_entity.to_dict()) if new_entity else "None",
                )
            ]

        elif name == "create_relation":
            new_relation = await KnowledgeGraphManager().create_relation(arguments)
            return [
                TextContent(
                    type="text",
                    text=json.dumps(new_relation.to_dict()) if new_relation else "None",
                )
            ]

        elif name == "add_observations":
            observations = await KnowledgeGraphManager().add_observations(arguments)
            return [
                TextContent(
                    type="text",
                    text=json.dumps(observations if observations else "None"),
                )
            ]

        elif name == "delete_entities":
            await KnowledgeGraphManager().delete_entities(arguments)
            return [TextContent(type="text", text="Entities deleted")]

        elif name == "delete_observations":
            await KnowledgeGraphManager().delete_observations(arguments)
            return [TextContent(type="text", text="Observations deleted")]

        elif name == "delete_relation":
            await KnowledgeGraphManager().delete_relation(arguments)
            return [TextContent(type="text", text="Relations deleted")]

        elif name == "read_graph":
            graph = await KnowledgeGraphManager().read_graph()
            graph_dict = {
                "entities": [entity.to_dict() for entity in graph.entities],
                "relations": [relation.to_dict() for relation in graph.relations],
            }
            return [TextContent(type="text", text=json.dumps(graph_dict))]

        elif name == "search_nodes":
            graph = await KnowledgeGraphManager().search_nodes(arguments)
            graph_dict = {
                "entities": [entity.to_dict() for entity in graph.entities],
                "relations": [relation.to_dict() for relation in graph.relations],
            }
            return [TextContent(type="text", text=json.dumps(graph_dict))]

        # TODO: Implement this method
        # elif name == "open_nodes":
        #     graph = await KnowledgeGraphManager().open_nodes(arguments["names"])
        #     graph_dict = {
        #         "entities": [entity.to_dict() for entity in graph.entities],
        #         "relations": [relation.to_dict() for relation in graph.relations],
        #     }
        #     return [TextContent(type="text", text=json.dumps(graph_dict))]

        else:
            raise Exception(f"Unknown tool name: {name}")

    except Exception as e:
        logger.error(f"Error handling tool {name}: {e}")
        logger.exception(e, stack_info=True)
        raise McpError(
            ErrorData(
                code=INTERNAL_ERROR,
                message=f"Error handling tool {name}: {e}",
            )
        )


def list_tools_sync() -> list[types.Tool]:
    return [
        types.Tool(
            name="create_entity",
            description="Create a new entity in the knowledge graph",
            inputSchema=Entity.schema(),
        ),
        # types.Tool(
        #     name="create_entities",
        #     description="Create multiple new entities in the knowledge graph",
        #     inputSchema={
        #         "type": "object",
        #         "properties": {
        #             "entities": {
        #                 "type": "array",
        #                 "items": {
        #                     "type": "object",
        #                     "properties": {
        #                         "name": {
        #                             "type": "string",
        #                             "description": "The name of the entity",
        #                         },
        #                         "entity_type": {
        #                             "type": "string",
        #                             "description": "The type of the entity",
        #                         },
        #                         "observations": {
        #                             "type": "array",
        #                             "items": {"type": "string"},
        #                             "description": "An array of observation contents associated with the entity",
        #                         },
        #                     },
        #                     "required": ["name", "entity_type", "observations"],
        #                 },
        #             },
        #         },
        #         "required": ["entities"],
        #     },
        # ),
        types.Tool(
            name="create_relation",
            description="Create multiple new relations between entities in the knowledge graph. Relations should be in active voice",
            inputSchema=Relation.schema(),
        ),
        types.Tool(
            name="add_observations",
            description="Add new observations to an existing entity in the knowledge graph",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_name": {
                        "type": "string",
                        "description": "The name of the entity to add the observations to",
                    },
                    "observations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "An array of observations to add",
                    },
                },
                "required": ["entity_name", "contents"],
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
                "required": ["deletions"],
            },
        ),
        types.Tool(
            name="delete_relation",
            description="Delete a relation from the knowledge graph",
            inputSchema={
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


def main():
    logger.info("Server is starting up")

    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]

    if ENTITIES_COLLECTION not in db.list_collection_names():
        logger.info("Creating entities collection")
        db.create_collection(ENTITIES_COLLECTION)

    if RELATIONS_COLLECTION not in db.list_collection_names():
        logger.info("Creating relations collection")
        db.create_collection(RELATIONS_COLLECTION)

    # async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
    #     await server.run(
    #         read_stream,
    #         write_stream,
    #         InitializationOptions(
    #             server_name="mcp_memory",
    #             server_version="0.1.0",
    #             capabilities=server.get_capabilities(
    #                 notification_options=NotificationOptions(),
    #                 experimental_capabilities={},
    #             ),
    #         ),
    #     )

    transport = "sse"
    if transport == "sse":
        logger.info("Using SSE transport")
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await server.run(
                    streams[0], streams[1], server.create_initialization_options()
                )

        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        import uvicorn

        # from fastapi import HTTPException, Request
        # async def validate_bearer_token(request: Request):
        #     auth_header = request.headers.get("Authorization")
        #     if auth_header is None or not auth_header.startswith("Bearer "):
        #         raise HTTPException(status_code=401, detail="Invalid or missing token")
        #     token = auth_header.split(" ")[1]
        #     # Add your token validation logic here
        #     if token != "your_expected_token":
        #         raise HTTPException(status_code=401, detail="Invalid token")
        # starlette_app.add_middleware(validate_bearer_token)
        uvicorn.run(starlette_app, host="0.0.0.0", port=8001)
    else:
        logger.info("Using stdio transport")
        from mcp.server.stdio import stdio_server

        async def arun():
            async with stdio_server() as streams:
                await server.run(
                    streams[0], streams[1], server.create_initialization_options()
                )

        anyio.run(arun)

    return 0


# if __name__ == "__main__":
#     mcp.run(transport="sse")
