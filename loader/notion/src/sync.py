import logging
from typing import Optional

from .api.notion import NotionAPI
from .parsers.block_parser import BlockParser
from .storage.chroma import ChromaStore
from .utils.logging import setup_logging
from .utils.text import TextProcessor

logger = setup_logging()


class NotionSync:
    """Orchestrates synchronization between Notion and ChromaDB."""

    def __init__(self, notion_api: NotionAPI, chroma_store: ChromaStore):
        """Initialize sync components.

        Args:
            notion_api: Initialized NotionAPI instance
            chroma_store: Initialized ChromaStore instance
        """
        self.notion_api = notion_api
        self.chroma_store = chroma_store
        self.block_parser = BlockParser()

    @staticmethod
    def should_skip(page: str) -> bool:
        """Check if page should be skipped based on content.

        Args:
            page: Page content to check

        Returns:
            True if page should be skipped, False otherwise
        """
        return "#skip" in page

    def process_page(self, notion_doc: dict) -> None:
        """Process a single Notion page.

        Args:
            notion_doc: Notion page data
        """
        notion_id = notion_doc.get("id")
        metadata = self.notion_api.get_page_metadata(notion_doc)
        title = metadata["title"]
        notion_last_updated = metadata["last_edited_time"]

        # Check if document exists in ChromaDB
        existing_doc = self.chroma_store.get_document(notion_id)

        # Get page content from Notion
        content = self.notion_api.get_page_content(notion_id)
        if not content:
            logger.error(f"Failed to get content for page: {title}")
            return

        # Parse blocks into markdown
        markdown_content = ""
        for block in content.get("results", []):
            parsed_block = self.block_parser.parse_block(block)
            if parsed_block:
                markdown_content += parsed_block + "\n"

        # Clean up markdown content
        markdown_content = TextProcessor.clean_markdown(markdown_content)

        # Handle empty documents
        if len(markdown_content) == 0:
            logger.warning(f"Removing empty document from Chroma: {title}")
            self.chroma_store.delete_document(notion_id)
            return

        # Handle skipped documents
        if self.should_skip(markdown_content):
            logger.warning(f"Removing skipped document from Chroma: {title}")
            self.chroma_store.delete_document(notion_id)
            return

        # Update document in ChromaDB if needed
        if not existing_doc:
            logger.info(f"Adding new document to Chroma: {title}")
            self.chroma_store.update_document(notion_id, markdown_content, title)
        else:
            chroma_last_updated = existing_doc["metadatas"][0]["last_updated"]

            if chroma_last_updated < str(notion_last_updated):
                logger.info(f"Updating modified document in Chroma: {title}")
                self.chroma_store.delete_document(notion_id)
                self.chroma_store.update_document(notion_id, markdown_content, title)
            else:
                logger.info(f"Document up to date in Chroma: {title}")

    def sync(self) -> None:
        """Synchronize all Notion pages with ChromaDB."""
        # Get all pages from Notion
        pages = self.notion_api.search_pages()
        if not pages:
            logger.error("Failed to retrieve pages from Notion")
            return

        # Process each page
        for page in pages.get("results", []):
            try:
                self.process_page(page)
            except Exception as e:
                logger.error(f"Error processing page {page.get('id')}: {str(e)}")
                continue

        # Log final document count
        all_docs = self.chroma_store.get_all_documents()
        logger.info(
            f"Sync complete. Total documents in Chroma: {len(all_docs['documents'])}"
        )
