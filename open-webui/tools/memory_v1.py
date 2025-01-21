"""
title: Memory Management
author: Tim
email:
date: 2025-01-19
version: 0.0.1
license:
requirements: pymongo>=4.10.1, python-dotenv>=1.0.1"
description: Manage memories
"""

import logging
import os
from typing import Annotated

from pydantic import BaseModel, Field
from pymongo import MongoClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# MONGO_URI = os.environ.get("MONGO_URI")
DATABASE_NAME = "memories"
ENTITIES_COLLECTION = "entities"
RELATIONS_COLLECTION = "relations"
MONGO_URI = "mongodb://test:test@localhost:27017/"


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

    def to_dict(self):
        return {"entities": self.entities, "relations": self.relations}


class Tools:
    def __init__(self, base_path=None):
        self.base_path = base_path if base_path else os.getcwd()

    def read_graph(self) -> KnowledgeGraph:
        logger.info("read_graph called")
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        entities = db[ENTITIES_COLLECTION].find()
        relations = db[RELATIONS_COLLECTION].find()
        graph = KnowledgeGraph(entities=entities, relations=relations)
        return graph

    def create_entity(self, entity_name: str, entity_type: str) -> Entity:
        logger.info(
            f"create_entity called with entity_name={entity_name}, entity_type={entity_type}"
        )
        entity = Entity(name=entity_name, entity_type=entity_type, observations=[])
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        entities_collection = db[ENTITIES_COLLECTION]
        if not entities_collection.find_one({"name": entity.name}):
            entities_collection.insert_one(entity.to_dict())
            return entity
        else:
            return None

    def create_relation(
        self, from_entity: str, to_entity: str, relation_type: str
    ) -> list[Relation]:
        logger.info(
            f"create_relation called with from_entity={from_entity}, to_entity={to_entity}, relation_type={relation_type}"
        )
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        relations_collection = db[RELATIONS_COLLECTION]

        if not relations_collection.find_one(
            {
                "from_entity": from_entity,
                "to_entity": to_entity,
                "relation_type": relation_type,
            }
        ):
            relation = Relation(
                from_entity=from_entity,
                to_entity=to_entity,
                relation_type=relation_type,
            )
            relations_collection.insert_one(relation.to_dict())
            return relation

        return None

    def add_observations(self, entity_name: str, observations: list[str]) -> dict:
        logger.info(
            f"add_observations called with entity_name={entity_name}, observations={observations}"
        )
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
            return {
                "entity_name": entity_name,
                "added_observations": new_observations,
            }
        else:
            raise Exception(f"Entity with name {entity_name} not found")

    def delete_entities(self, entity_names: list[str]) -> None:
        logger.info(f"delete_entities called with entity_names={entity_names}")
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

    def delete_observations(self, entity_name: str, observations: list[str]) -> None:
        logger.info(
            f"delete_observations called with entity_name={entity_name}, observations={observations}"
        )
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        entities_collection = db[ENTITIES_COLLECTION]

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

    def delete_relation(
        self, from_entity: str, to_entity: str, relation_type: str
    ) -> None:
        logger.info(
            f"delete_relation called with from_entity={from_entity}, to_entity={to_entity}, relation_type={relation_type}"
        )
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        relations_collection = db[RELATIONS_COLLECTION]

        relation = Relation(
            from_entity=from_entity, to_entity=to_entity, relation_type=relation_type
        )

        relations_collection.delete_one(relation.to_dict())

    def search_nodes(self, query: str) -> KnowledgeGraph:
        logger.info(f"search_nodes called with query={query}")
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        entities_collection = db[ENTITIES_COLLECTION]
        relations_collection = db[RELATIONS_COLLECTION]

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
