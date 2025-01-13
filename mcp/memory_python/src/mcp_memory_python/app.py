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
            "relationType": self.relation_type,
        }


class KnowledgeGraph:
    def __init__(self):
        self.entities = []
        self.relations = []

    # def save_to_mongodb(self):
    #     client = MongoClient(MONGO_URI)
    #     db = client[DATABASE_NAME]
    #     entities_collection = db[ENTITIES_COLLECTION]
    #     relations_collection = db[RELATIONS_COLLECTION]

    #     # Clear existing data
    #     entities_collection.delete_many({})
    #     relations_collection.delete_many({})

    #     # Insert entities and relations
    #     entities_collection.insert_many([entity.to_dict() for entity in self.entities])
    #     relations_collection.insert_many(
    #         [relation.to_dict() for relation in self.relations]
    #     )

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
            Relation(relation["from"], relation["to"], relation["relationType"])
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

    async def create_entities(self, entities: list[Entity]) -> list[Entity]:
        graph = await self.load_graph()

        new_entities = []
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        entities_collection = db[ENTITIES_COLLECTION]

        for entity in entities:
            if not entities_collection.find_one({"name": entity.name}):
                entities_collection.insert_one(entity.to_dict())
                new_entities.append(entity)

        return new_entities

        graph.entities.extend(entities)
        # graph.save_to_mongodb()

    async def readGraph(self) -> KnowledgeGraph:
        return self.loadGraph()


#       async createEntities(entities: Entity[]): Promise<Entity[]> {
#     const graph = await this.loadGraph();
#     const newEntities = entities.filter(
#       (e) =>
#         !graph.entities.some((existingEntity) => existingEntity.name === e.name)
#     );
#     graph.entities.push(...newEntities);
#     await this.saveGraph(graph);
#     return newEntities;
#   }

#   async createRelations(relations: Relation[]): Promise<Relation[]> {
#     const graph = await this.loadGraph();
#     const newRelations = relations.filter(
#       (r) =>
#         !graph.relations.some(
#           (existingRelation) =>
#             existingRelation.from === r.from &&
#             existingRelation.to === r.to &&
#             existingRelation.relationType === r.relationType
#         )
#     );
#     graph.relations.push(...newRelations);
#     await this.saveGraph(graph);
#     return newRelations;
#   }

#   async addObservations(
#     observations: { entityName: string; contents: string[] }[]
#   ): Promise<{ entityName: string; addedObservations: string[] }[]> {
#     const graph = await this.loadGraph();
#     console.log("observations:", observations);
#     console.log("Type of observations:", typeof observations);
#     const results = observations.map((o) => {
#       const entity = graph.entities.find((e) => e.name === o.entityName);
#       if (!entity) {
#         throw new Error(`Entity with name ${o.entityName} not found`);
#       }
#       const newObservations = o.contents.filter(
#         (content) => !entity.observations.includes(content)
#       );
#       entity.observations.push(...newObservations);
#       return { entityName: o.entityName, addedObservations: newObservations };
#     });
#     await this.saveGraph(graph);
#     return results;
#   }

#   async deleteEntities(entityNames: string[]): Promise<void> {
#     const graph = await this.loadGraph();
#     graph.entities = graph.entities.filter(
#       (e) => !entityNames.includes(e.name)
#     );
#     graph.relations = graph.relations.filter(
#       (r) => !entityNames.includes(r.from) && !entityNames.includes(r.to)
#     );
#     await this.saveGraph(graph);
#   }

#   async deleteObservations(
#     deletions: { entityName: string; observations: string[] }[]
#   ): Promise<void> {
#     const graph = await this.loadGraph();
#     deletions.forEach((d) => {
#       const entity = graph.entities.find((e) => e.name === d.entityName);
#       if (entity) {
#         entity.observations = entity.observations.filter(
#           (o) => !d.observations.includes(o)
#         );
#       }
#     });
#     await this.saveGraph(graph);
#   }

#   async deleteRelations(relations: Relation[]): Promise<void> {
#     const graph = await this.loadGraph();
#     graph.relations = graph.relations.filter(
#       (r) =>
#         !relations.some(
#           (delRelation) =>
#             r.from === delRelation.from &&
#             r.to === delRelation.to &&
#             r.relationType === delRelation.relationType
#         )
#     );
#     await this.saveGraph(graph);
#   }

#   async readGraph(): Promise<KnowledgeGraph> {
#     return this.loadGraph();
#   }

#   // Very basic search function
#   async searchNodes(query: string): Promise<KnowledgeGraph> {
#     const graph = await this.loadGraph();

#     // Filter entities
#     const filteredEntities = graph.entities.filter(
#       (e) =>
#         e.name.toLowerCase().includes(query.toLowerCase()) ||
#         e.entityType.toLowerCase().includes(query.toLowerCase()) ||
#         e.observations.some((o) =>
#           o.toLowerCase().includes(query.toLowerCase())
#         )
#     );

#     // Create a Set of filtered entity names for quick lookup
#     const filteredEntityNames = new Set(filteredEntities.map((e) => e.name));

#     // Filter relations to only include those between filtered entities
#     const filteredRelations = graph.relations.filter(
#       (r) => filteredEntityNames.has(r.from) && filteredEntityNames.has(r.to)
#     );

#     const filteredGraph: KnowledgeGraph = {
#       entities: filteredEntities,
#       relations: filteredRelations,
#     };

#     return filteredGraph;
#   }

#   async openNodes(names: string[]): Promise<KnowledgeGraph> {
#     const graph = await this.loadGraph();

#     // Filter entities
#     const filteredEntities = graph.entities.filter((e) =>
#       names.includes(e.name)
#     );

#     // Create a Set of filtered entity names for quick lookup
#     const filteredEntityNames = new Set(filteredEntities.map((e) => e.name));

#     // Filter relations to only include those between filtered entities
#     const filteredRelations = graph.relations.filter(
#       (r) => filteredEntityNames.has(r.from) && filteredEntityNames.has(r.to)
#     );

#     const filteredGraph: KnowledgeGraph = {
#       entities: filteredEntities,
#       relations: filteredRelations,
#     };

#     return filteredGraph;
#   }


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
                                "from": {
                                    "type": "string",
                                    "description": "The name of the entity where the relation starts",
                                },
                                "to": {
                                    "type": "string",
                                    "description": "The name of the entity where the relation ends",
                                },
                                "relationType": {
                                    "type": "string",
                                    "description": "The type of the relation",
                                },
                            },
                            "required": ["from", "to", "relationType"],
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
                                "entityName": {
                                    "type": "string",
                                    "description": "The name of the entity to add the observations to",
                                },
                                "contents": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "An array of observation contents to add",
                                },
                            },
                            "required": ["entityName", "contents"],
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
                    "entityNames": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "An array of entity names to delete",
                    },
                },
                "required": ["entityNames"],
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
                                "entityName": {
                                    "type": "string",
                                    "description": "The name of the entity containing the observations",
                                },
                                "observations": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "An array of observations to delete",
                                },
                            },
                            "required": ["entityName", "observations"],
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
                                "from": {
                                    "type": "string",
                                    "description": "The name of the entity where the relation starts",
                                },
                                "to": {
                                    "type": "string",
                                    "description": "The name of the entity where the relation ends",
                                },
                                "relationType": {
                                    "type": "string",
                                    "description": "The type of the relation",
                                },
                            },
                            "required": ["from", "to", "relationType"],
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
