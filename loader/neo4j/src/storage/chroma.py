import hashlib
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Union

import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

from ..config import Config
from ..llm.chunker import TextChunk

logger = logging.getLogger(__name__)


class ChromaStore:
    def __init__(self):
        self.vector_store = self._initialize_chroma_client()

    def _initialize_chroma_client(self) -> Chroma:
        """Initialize ChromaDB client with proper configuration.

        Returns:
            Configured Chroma client instance
        """
        chroma_client = chromadb.HttpClient(
            settings=Settings(
                anonymized_telemetry=False,
                chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
                chroma_client_auth_credentials=Config.REQUIRED_ENV_VARS[
                    "CHROMA_AUTH_TOKEN"
                ],
            ),
            host=Config.REQUIRED_ENV_VARS["CHROMA_HOST"],
            port="443",
            ssl=True,
        )
        chroma_client.heartbeat()

        embeddings = OllamaEmbeddings(
            base_url=f"https://{Config.REQUIRED_ENV_VARS['OLLAMA_HOST']}",
            model="nomic-embed-text",
        )

        collection_name = Config.REQUIRED_ENV_VARS["CHROMA_COLLECTION"]
        chroma_client.get_or_create_collection(collection_name)

        return Chroma(
            client=chroma_client,
            collection_name=collection_name,
            embedding_function=embeddings,
        )

    def delete_document(self, notion_id: str) -> None:
        """Delete all chunks associated with a document.

        Args:
            notion_id: Notion page ID to delete
        """
        results = self.vector_store.get(where={"notion_id": {"$eq": notion_id}})
        if (
            "ids" in results and results["ids"]
        ):  # Check if there are actually IDs to delete
            logger.info(
                f"Deleting {len(results['ids'])} chunks for document {notion_id}"
            )
            self.vector_store.delete(ids=results["ids"])
        else:
            logger.info(f"No chunks found to delete for document {notion_id}")

    def get_document_hash(self, content: str) -> str:
        """Generate hash of document content.

        Args:
            content: Document content to hash

        Returns:
            SHA-256 hash of content
        """
        return hashlib.sha256(content.encode()).hexdigest()

    def update_document(
        self, notion_id: str, chunks: List[Union[str, TextChunk]], title: str
    ) -> None:
        """Update or create document chunks in vector store.

        Args:
            notion_id: Notion page ID
            chunks: List of pre-generated chunks (either strings or TextChunk objects)
            title: Document title
        """
        logger.debug(f"Storing {len(chunks)} chunks in Chroma")

        for index, chunk in enumerate(chunks):
            chunk_text = chunk.text if hasattr(chunk, "text") else chunk
            document = Document(
                page_content=chunk_text,
                metadata={
                    "title": title,
                    "last_updated": str(datetime.now()),
                    "notion_id": notion_id,
                    "chunk_number": index,
                },
                id=str(uuid.uuid4()),
            )

            self.vector_store.add_documents([document])

        logger.info("Document has been updated in Chroma.")

    def get_document_chunks(self, notion_id: str) -> List[Dict]:
        """Get all chunks for a document.

        Args:
            notion_id: Notion page ID

        Returns:
            List of document chunks with metadata
        """
        return self.vector_store.get(where={"notion_id": {"$eq": notion_id}})

    def get_document_metadata(self, notion_id: str) -> Optional[Dict]:
        """Get metadata for a document.

        Args:
            notion_id: Notion page ID

        Returns:
            Document metadata if found, None otherwise
        """
        chunks = self.get_document_chunks(notion_id)
        if chunks and chunks["metadatas"]:
            return chunks["metadatas"][0]
        return None

    def clear_collection(self) -> None:
        """Clear the entire vector store collection."""
        self.vector_store.delete_collection()
        logger.info("Vector store collection cleared.")
