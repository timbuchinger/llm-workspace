import logging
import time
from datetime import datetime
from typing import Optional

from langchain_ollama import OllamaEmbeddings

from .api.notion import NotionAPI
from .config import Config
from .llm.extractor import RelationshipExtractor
from .storage.chroma import ChromaStore
from .storage.neo4j import Neo4jStore
from .utils.stats import SyncStats
from .utils.text import clean_markdown, should_skip_document, split_text

logger = logging.getLogger(__name__)


class NotionSync:
    def __init__(self):
        self.stats = SyncStats()
        self.notion = NotionAPI()
        self.chroma = ChromaStore()
        self.neo4j = Neo4jStore()
        self.embeddings = OllamaEmbeddings(
            base_url=f"https://{Config.REQUIRED_ENV_VARS['OLLAMA_HOST']}",
            model="nomic-embed-text",
        )
        self.extractor = RelationshipExtractor()

    def initialize_storage(self) -> None:
        """Initialize storage backends before sync."""
        self.neo4j._initialize_database()
        logger.info("Storage backends initialized")

    def _process_page(self, page_id: str, page_data: dict) -> None:
        """Process a single Notion page.

        Args:
            page_id: Notion page ID
            page_data: Page data from Notion API
        """
        # Get page content and metadata
        title = self.notion.get_page_title(page_data)
        logger.info(f"Starting to process document: {title} ({page_id})")
        markdown_content = self.notion.get_page_markdown(page_id)

        if not markdown_content:
            logger.warning(f"Empty content for page: {title} ({page_id})")
            self._clean_empty_document(page_id)
            return

        markdown_content = clean_markdown(markdown_content)

        if should_skip_document(markdown_content):
            logger.warning(f"Skipping page marked with #skip: {title} ({page_id})")
            self._clean_empty_document(page_id)
            self.stats.documents_skipped += 1
            self.stats.documents_processed += 1
            logger.info(
                f"{self.stats.documents_processed} of {self.stats.total_documents} files processed"
            )
            return

        final_content = f"# {title}\n\n{markdown_content}"
        content_hash = self.chroma.get_document_hash(final_content)
        stored_hash = self.neo4j.get_note_hash(page_id)

        # Check if document needs updating
        if not self._should_update_document(
            page_data, page_id, stored_hash, content_hash
        ):
            logger.info(f"Document is up to date: {title} ({page_id})")
            self.stats.documents_processed += 1
            logger.info(
                f"{self.stats.documents_processed} of {self.stats.total_documents} files processed"
            )
            return

        logger.info(f"Updating document: {title} ({page_id})")

        # Generate embeddings and extract relationships
        embedding = self.embeddings.embed_query(final_content)
        relationships = self.extractor.process_document(title, markdown_content)

        # Clean existing data
        # Track deletions
        self.neo4j.clean_document(page_id)
        self.stats.neo4j_deletions += 1

        self.chroma.delete_document(page_id)
        self.stats.chroma_deletions += 1

        # Generate chunks once to use for both storage systems
        logger.info("Generating semantic chunks...")
        chunks = split_text(final_content, use_semantic=True, stats=self.stats)
        chunk_texts = [
            chunk.text if hasattr(chunk, "text") else chunk for chunk in chunks
        ]

        # Update Neo4j with chunks and metadata
        self.neo4j.create_note(page_id, title, final_content, embedding)
        self.stats.neo4j_nodes_created += 1

        self.neo4j.create_chunks(page_id, chunk_texts)
        self.stats.neo4j_nodes_created += len(chunk_texts)

        # Store chunk summaries if available
        for i, chunk in enumerate(chunks):
            if hasattr(chunk, "summary") and chunk.summary:
                self.neo4j.create_chunk_summary(page_id, i, chunk.summary)

        self.neo4j.create_relationships(page_id, relationships)
        self.stats.neo4j_relationships_created += len(relationships)

        # Update Chroma with the pre-generated chunks
        self.chroma.update_document(page_id, chunks, title)
        self.stats.chroma_insertions += len(chunks)

        self.stats.documents_processed += 1
        logger.info(
            f"{self.stats.documents_processed} of {self.stats.total_documents} files processed"
        )
        logger.info(f"Document successfully processed: {title} ({page_id})")

    def _clean_empty_document(self, notion_id: str) -> None:
        """Clean up empty or skipped documents from storage.

        Args:
            notion_id: Notion page ID
        """
        self.chroma.delete_document(notion_id)
        self.stats.chroma_deletions += 1

        self.neo4j.clean_document(notion_id)
        self.stats.neo4j_deletions += 1

    def _should_update_document(
        self,
        page_data: dict,
        notion_id: str,
        stored_hash: Optional[str],
        current_hash: str,
    ) -> bool:
        """Check if document needs updating.

        Args:
            page_data: Page data from Notion API
            notion_id: Notion page ID
            stored_hash: Hash of stored content
            current_hash: Hash of current content

        Returns:
            True if document should be updated, False otherwise
        """
        # Always update if no stored hash
        if not stored_hash:
            return True

        # Check content hash
        if stored_hash != current_hash:
            return True

        # Check last modified time
        try:
            notion_last_updated = datetime.strptime(
                page_data.get("last_edited_time"), "%Y-%m-%dT%H:%M:%S.%fZ"
            )

            chroma_metadata = self.chroma.get_document_metadata(notion_id)
            if not chroma_metadata:
                return True

            chroma_last_updated = datetime.strptime(
                chroma_metadata["last_updated"], "%Y-%m-%d %H:%M:%S.%f"
            )

            return chroma_last_updated < notion_last_updated
        except (ValueError, KeyError, TypeError):
            # If we can't parse dates, update to be safe
            return True

    def sync(self) -> None:
        """Synchronize all Notion pages to ChromaDB and Neo4j."""
        logger.info("Starting Notion sync...")

        try:
            # Initialize storage before processing any pages
            self.initialize_storage()

            pages = self.notion.search_pages()
            self.stats.total_documents = len(pages)
            logger.info(f"Found {len(pages)} pages to process")

            for page in pages:
                try:
                    self._process_page(page.get("id"), page)
                except Exception as e:
                    logger.error(f"Error processing page {page.get('id')}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Sync failed: {str(e)}")
            raise
        finally:
            self.neo4j.close()
            self.stats.mark_complete()

        logger.info("Sync completed successfully")
        logger.info("\n" + self.stats.generate_report())

    def clear_databases(self) -> None:
        """Clear both ChromaDB and Neo4j databases."""
        logger.info("Clearing databases...")
        self.chroma.clear_collection()
        self.neo4j.clean_document("*")  # Wildcard to clean all documents
        logger.info("Databases cleared")
