import json
import os

# Define the path to the JSONL file, you can change this to your desired local path
__dirname = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE_PATH = os.path.join(__dirname, "memory.json")


# We are storing our memory using entities, relations, and observations in a graph structure
class Entity:
    def __init__(self, name: str, entity_type: str, observations: list):
        self.name = name
        self.entity_type = entity_type
        self.observations = observations


class Relation:
    def __init__(self, from_entity: str, to_entity: str, relation_type: str):
        self.from_entity = from_entity
        self.to_entity = to_entity
        self.relation_type = relation_type


class KnowledgeGraph:
    def __init__(self):
        self.entities = []
        self.relations = []


class KnowledgeGraphManager:
    async def load_graph(self) -> KnowledgeGraph:
        try:
            with open(MEMORY_FILE_PATH, "r", encoding="utf-8") as file:
                data = file.read()
                lines = [line for line in data.split("\n") if line.strip() != ""]
                graph = KnowledgeGraph()
                for line in lines:
                    # Assuming the JSONL file contains JSON objects for entities and relations
                    obj = json.loads(line)
                    if "entityType" in obj:
                        entity = Entity(
                            obj["name"], obj["entityType"], obj["observations"]
                        )
                        graph.entities.append(entity)
                    elif "relationType" in obj:
                        relation = Relation(obj["from"], obj["to"], obj["relationType"])
                        graph.relations.append(relation)
                return graph
        except Exception as e:
            print(f"Error loading graph: {e}")
            return KnowledgeGraph()
