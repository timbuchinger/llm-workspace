"""Text processing utilities."""

import logging
import re
from typing import List, Optional, Union

import tiktoken

from ..llm.chunker import ChunkingLLM, TextChunk
from .stats import SyncStats

logger = logging.getLogger(__name__)


def split_text(
    text: str,
    use_semantic: bool = True,
    max_tokens: int = 300,
    overlap: int = 50,
    stats: Optional[SyncStats] = None,
) -> Union[List[str], List[TextChunk]]:
    """Split text into chunks using either semantic or token-based approach.

    Args:
        text: Text to split
        use_semantic: Whether to use semantic chunking (LLM-based)
        max_tokens: Maximum number of tokens per chunk (for token-based)
        overlap: Number of tokens to overlap between chunks (for token-based)

    Returns:
        List of either text chunks (token-based) or TextChunk objects (semantic)
    """
    if use_semantic:
        try:
            chunker = ChunkingLLM()
            chunks = chunker.chunk_text(text)

            if chunker.validate_chunks(chunks):
                logger.debug("Successfully created semantic chunks")
                if stats:
                    stats.llm_chunked_docs += 1
                    stats.llm_chunks_created += len(chunks)
                return chunks

            logger.warning(
                "Semantic chunks failed validation, falling back to token-based"
            )
        except Exception as e:
            logger.warning(
                f"Semantic chunking failed: {str(e)}, falling back to token-based"
            )
            if stats:
                stats.rate_limit_hits += 1

    # Token-based fallback
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens = tokenizer.encode(text)
    chunks = []

    for i in range(0, len(tokens), max_tokens - overlap):
        chunk = tokens[i : i + max_tokens]
        chunk_text = tokenizer.decode(chunk)
        chunks.append(TextChunk(text=chunk_text) if use_semantic else chunk_text)

    if stats and use_semantic:
        stats.token_chunked_docs += 1
        stats.token_chunks_created += len(chunks)
    return chunks


def clean_markdown(text: str) -> str:
    """Clean and normalize markdown text.

    Args:
        text: Markdown text to clean

    Returns:
        Cleaned markdown text
    """
    # Strip text
    text = text.strip()

    # Replace multiple newlines with double newline
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text


def should_skip_document(text: str) -> bool:
    """Check if document should be skipped based on content.

    Args:
        text: Document content

    Returns:
        True if document should be skipped, False otherwise
    """
    return "#skip" in text
