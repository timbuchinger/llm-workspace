"""Text chunking using LLM for semantic chunking."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import tiktoken
from langchain.prompts import PromptTemplate
from langchain.schema.language_model import BaseLanguageModel

from ..config import Config
from .provider import get_llm

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """Representation of a text chunk with metadata."""

    text: str
    summary: Optional[str] = None
    token_count: Optional[int] = None


class ChunkingLLM:
    """LLM-based text chunking."""

    def __init__(self, llm: Optional[BaseLanguageModel] = None):
        """Initialize the chunking LLM.

        Args:
            llm: Optional language model instance. If not provided,
                 uses the default provider from config.
        """
        self.llm = llm or get_llm()

        # Load chunking prompt
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "chunking.txt"
        with open(prompt_path) as f:
            prompt_text = f.read()

        self.prompt = PromptTemplate.from_template(
            prompt_text + "\nText to chunk:\n{text}"
        )

    def chunk_text(self, text: str) -> List[TextChunk]:
        """Split text into semantic chunks using LLM.

        Args:
            text: Text content to chunk

        Returns:
            List of TextChunk objects containing chunks and metadata
        """
        chain = self.prompt | self.llm
        # Add guidance for response format
        formatted_prompt = (
            self.prompt.format(text=text)
            + """

Format your response as follows:

CHUNK 1 SUMMARY:
[1-2 sentence summary of chunk]

CHUNK 1 CONTENT:
[chunk content]

CHUNK 2 SUMMARY:
[1-2 sentence summary of chunk]

CHUNK 2 CONTENT:
[chunk content]

And so on for each chunk...
"""
        )
        response = chain.invoke({"text": formatted_prompt})

        # Extract content from AIMessage or string response
        content = response.content if hasattr(response, "content") else str(response)

        # Parse response and extract chunks with summaries
        chunks = []
        current_summary = None
        current_content = []

        for line in content.split("\n"):
            line = line.strip()

            if not line:
                continue

            if line.startswith("CHUNK") and "SUMMARY:" in line:
                # If we have an existing chunk, save it
                if current_content and current_summary:
                    chunks.append(
                        TextChunk(
                            text="\n".join(current_content), summary=current_summary
                        )
                    )
                    current_content = []
                current_summary = None
            elif line.startswith("CHUNK") and "CONTENT:" in line:
                continue
            elif current_summary is None:
                current_summary = line
            else:
                current_content.append(line)

        # Add the last chunk
        if current_content and current_summary:
            chunks.append(
                TextChunk(text="\n".join(current_content), summary=current_summary)
            )

        # Log chunks at debug level
        if chunks:
            logger.debug(f"Created {len(chunks)} chunks:")
            for i, chunk in enumerate(chunks, 1):
                logger.debug(f"Chunk {i}:")
                logger.debug(f"Summary: {chunk.summary}")
                logger.debug(f"Content: {chunk.text}\n")

        # If parsing failed, fallback to single chunk
        if not chunks:
            logger.warning("Failed to parse LLM chunks, falling back to single chunk")
            return [TextChunk(text=text)]

        return chunks

    @staticmethod
    def validate_chunks(chunks: List[TextChunk]) -> bool:
        """Validate chunks meet requirements.

        Args:
            chunks: List of chunks to validate

        Returns:
            True if chunks are valid, False otherwise
        """
        if not chunks:
            return False

        # Validate chunks
        if not chunks:
            return False

        # Check chunk sizes are reasonable (between 100 and 1000 tokens)
        tokenizer = tiktoken.get_encoding("cl100k_base")
        for i, chunk in enumerate(chunks, 1):
            token_count = len(tokenizer.encode(chunk.text))
            logger.debug(f"Chunk {i} token count: {token_count}")
            if token_count < 50 or token_count > 1000:
                logger.warning(
                    f"Chunk size {token_count} tokens is outside ideal range"
                )
                return False

        # Verify all chunks have summaries
        if not all(chunk.summary for chunk in chunks):
            return False

        return True
