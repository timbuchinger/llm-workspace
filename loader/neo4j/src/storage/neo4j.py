import logging
from typing import Dict, List, Optional

from neo4j import GraphDatabase

from ..config import Config

logger = logging.getLogger(__name__)


class Neo4jStore:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            Config.REQUIRED_ENV_VARS["NEO4J_URI"],
            auth=(
                Config.REQUIRED_ENV_VARS["NEO4J_USER"],
                Config.REQUIRED_ENV_VARS["NEO4J_PASSWORD"],
            ),
        )
        self.database = Config.REQUIRED_ENV_VARS["NEO4J_DATABASE"]
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Initialize Neo4j database with required constraints.

        Note: The database must be created manually through Neo4j's admin tools
        before running this script.
        """
        with self.driver.session(database=self.database) as session:
            try:
                # Set up constraints and indexes
                session.run(
                    "CREATE CONSTRAINT note_id IF NOT EXISTS FOR (n:Note) REQUIRE n.id IS UNIQUE"
                )
                session.run(
                    "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:NoteChunk) REQUIRE c.id IS UNIQUE"
                )
                session.run(
                    "CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE"
                )
                logger.info(
                    f"Neo4j database '{self.database}' initialized with constraints"
                )
            except Exception as e:
                logger.error(f"Error setting up Neo4j constraints: {str(e)}")
                raise

    def clean_document(self, notion_id: str) -> None:
        """Remove all nodes and relationships for a document.

        Args:
            notion_id: Notion page ID
        """
        with self.driver.session(database=self.database) as session:
            session.run(
                """
                MATCH (n:Note {id: $notion_id})
                OPTIONAL MATCH (n)-[:HAS_CHUNK]->(chunk:NoteChunk)
                OPTIONAL MATCH (chunk)-[next:NEXT_CHUNK]->()
                OPTIONAL MATCH (n)-[:CONTAINS]->(e:Entity)
                OPTIONAL MATCH (e)-[r:RELATION {note_id: $notion_id}]->(o:Entity)
                DETACH DELETE n, chunk, next, r
                WITH e, o
                WHERE NOT EXISTS((e)<-[:CONTAINS]-(:Note)) AND NOT EXISTS((o)<-[:CONTAINS]-(:Note))
                DELETE e, o
                """,
                notion_id=notion_id,
            )

    def create_note(
        self, notion_id: str, title: str, content: str, embedding: List[float]
    ) -> None:
        """Create a new note node.

        Args:
            notion_id: Notion page ID
            title: Note title
            content: Note content
            embedding: Vector embedding of content
        """
        with self.driver.session(database=self.database) as session:
            session.run(
                """
                CREATE (n:Note {
                    id: $notion_id,
                    title: $title,
                    content: $content,
                    embedding: $embedding
                })
                """,
                notion_id=notion_id,
                title=title,
                content=content,
                embedding=embedding,
            )

    def create_chunks(self, notion_id: str, chunks: List[str]) -> None:
        """Create note chunk nodes and relationships.

        Args:
            notion_id: Parent note ID
            chunks: List of text chunks
        """
        with self.driver.session(database=self.database) as session:
            previous_chunk_id = None

            for i, chunk_content in enumerate(chunks):
                chunk_id = f"{notion_id}-chunk-{i}"

                # Create chunk node
                session.run(
                    """
                    MATCH (n:Note {id: $notion_id})
                    CREATE (c:NoteChunk {
                        id: $chunk_id,
                        content: $content,
                        parentNote: $notion_id,
                        chunkNumber: $chunk_number
                    })
                    CREATE (n)-[:HAS_CHUNK]->(c)
                    """,
                    notion_id=notion_id,
                    chunk_id=chunk_id,
                    content=chunk_content,
                    chunk_number=i,
                )

                # Create NEXT_CHUNK relationship if not the first chunk
                if previous_chunk_id:
                    session.run(
                        """
                        MATCH (prev:NoteChunk {id: $prev_id})
                        MATCH (curr:NoteChunk {id: $curr_id})
                        CREATE (prev)-[:NEXT_CHUNK]->(curr)
                        """,
                        prev_id=previous_chunk_id,
                        curr_id=chunk_id,
                    )

                previous_chunk_id = chunk_id

    def create_relationships(
        self, notion_id: str, relationships: List[Dict[str, str]]
    ) -> None:
        """Create entity nodes and relationships.

        Args:
            notion_id: Parent note ID
            relationships: List of relationship dictionaries
        """
        with self.driver.session(database=self.database) as session:
            for rel in relationships:
                try:
                    # Defensive validation
                    if not all(
                        isinstance(rel.get(k), str) and rel.get(k)
                        for k in ["subject", "relationship", "object"]
                    ):
                        logger.warning(f"Skipping invalid relationship: {rel}")
                        continue

                    subject, relation, obj = (
                        rel["subject"].strip(),
                        rel["relationship"].strip(),
                        rel["object"].strip(),
                    )

                    # Additional validation
                    if not all([subject, relation, obj]):
                        logger.warning(
                            f"Skipping relationship with empty values: {rel}"
                        )
                        continue

                    # Execute Neo4j operation
                    try:
                        session.run(
                            """
                            MATCH (n:Note {id: $notion_id})
                            MERGE (s:Entity {name: $subject})
                            MERGE (o:Entity {name: $object})
                            MERGE (n)-[:CONTAINS]->(s)
                            MERGE (n)-[:CONTAINS]->(o)
                            MERGE (s)-[r:RELATION {type: $relation, note_id: $notion_id}]->(o)
                            """,
                            notion_id=notion_id,
                            subject=subject,
                            relation=relation,
                            object=obj,
                        )
                    except Exception as e:
                        logger.error(
                            f"Neo4j operation failed for relationship {rel}: {str(e)}"
                        )
                        continue
                except (KeyError, AttributeError) as e:
                    logger.error(f"Failed to process relationship {rel}: {str(e)}")
                    continue

    def get_note_hash(self, notion_id: str) -> Optional[str]:
        """Get the stored hash for a note.

        Args:
            notion_id: Note ID

        Returns:
            Stored hash if found, None otherwise
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(
                """
                MATCH (n:Note {id: $notion_id})
                RETURN n.hash as hash
                """,
                notion_id=notion_id,
            ).single()

            return result["hash"] if result else None

    def create_chunk_summary(
        self, notion_id: str, chunk_number: int, summary: str
    ) -> None:
        """Update a chunk node with its summary.

        Args:
            notion_id: Parent note ID
            chunk_number: Index of the chunk
            summary: Summary text for the chunk
        """
        chunk_id = f"{notion_id}-chunk-{chunk_number}"
        with self.driver.session(database=self.database) as session:
            session.run(
                """
                MATCH (c:NoteChunk {id: $chunk_id})
                SET c.summary = $summary
                """,
                chunk_id=chunk_id,
                summary=summary,
            )

    def close(self) -> None:
        """Close the database driver."""
        self.driver.close()
