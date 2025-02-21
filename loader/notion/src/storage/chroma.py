import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

from ..utils.logging import setup_logging
from ..utils.text import TextProcessor

logger = setup_logging()


class ChromaStore:
    """Handler for ChromaDB operations."""

    def __init__(self):
        """Initialize ChromaDB connection and collection."""
        self.client = self._initialize_client()
        self.vector_store = self._initialize_vector_store()

    def _initialize_client(self) -> chromadb.HttpClient:
        """Initialize ChromaDB client with authentication.

        Returns:
            Configured ChromaDB client
        """
        client = chromadb.HttpClient(
            settings=Settings(
                anonymized_telemetry=False,
                chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
                chroma_client_auth_credentials=os.environ.get("CHROMA_AUTH_TOKEN"),
            ),
            host=os.environ.get("CHROMA_HOST"),
            port="443",
            ssl=True,
        )
        client.heartbeat()
        return client

    def _initialize_vector_store(self) -> Chroma:
        """Initialize LangChain Chroma vector store.

        Returns:
            Configured Chroma vector store
        """
        embeddings = OllamaEmbeddings(
            base_url=f"https://{os.environ.get('OLLAMA_HOST')}",
            model="nomic-embed-text",
        )

        self.client.get_or_create_collection("notion")

        return Chroma(
            client=self.client,
            collection_name="notion",
            embedding_function=embeddings,
        )

    def delete_document(self, notion_id: str) -> None:
        """Delete all chunks of a document from ChromaDB.

        Args:
            notion_id: Unique identifier of the Notion document
        """
        children = self.vector_store.get(where={"notion_id": {"$eq": notion_id}})
        logger.info(f"Deleting {len(children['documents'])} chunks...")

        for child in children["documents"]:
            logger.info(f"Deleting chunk: {child.id}")
            self.vector_store.delete(ids=[child.id])

    def update_document(
        self, notion_id: str, markdown_content: str, title: str
    ) -> None:
        """Update document content in ChromaDB.

        Args:
            notion_id: Unique identifier of the Notion document
            markdown_content: Markdown formatted content to store
            title: Document title
        """
        chunks = TextProcessor.split_text(markdown_content)
        logger.info(f"Split into {len(chunks)} chunks.")

        documents = []
        for index, chunk in enumerate(chunks):
            logger.debug(f"Processing chunk #{index}...")
            document = Document(
                page_content=chunk,
                metadata={
                    "title": title,
                    "last_updated": str(datetime.now()),
                    "notion_id": notion_id,
                    "chunk_number": index,
                },
            )
            documents.append(document)

        self.vector_store.add_documents(documents)
        logger.info("Document chunks added to ChromaDB.")

    def get_document(self, notion_id: str) -> Optional[Dict]:
        """Retrieve a document from ChromaDB.

        Args:
            notion_id: Unique identifier of the Notion document

        Returns:
            Document data or None if not found
        """
        results = self.vector_store.get(where={"notion_id": {"$eq": notion_id}})
        return results if results["documents"] else None

    def get_all_documents(self) -> Dict:
        """Retrieve all documents from ChromaDB.

        Returns:
            All documents in the collection
        """
        return self.vector_store.get()

    def clear_collection(self) -> None:
        """Delete all documents from the collection."""
        self.vector_store.delete_collection()
        logger.info("Collection cleared.")
