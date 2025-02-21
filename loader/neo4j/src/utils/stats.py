"""Statistics tracking utilities."""

import time
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SyncStats:
    """Statistics for sync operations."""

    start_time: float = field(default_factory=time.time)
    end_time: float = None

    # Database operations
    chroma_insertions: int = 0
    chroma_updates: int = 0
    chroma_deletions: int = 0
    neo4j_nodes_created: int = 0
    neo4j_relationships_created: int = 0
    neo4j_deletions: int = 0

    # Chunking statistics
    llm_chunked_docs: int = 0
    token_chunked_docs: int = 0
    llm_chunks_created: int = 0
    token_chunks_created: int = 0

    # Rate limiting statistics
    rate_limit_hits: int = 0
    rate_limit_wait_time: float = 0.0

    # Document statistics
    total_documents: int = 0
    documents_processed: int = 0
    documents_skipped: int = 0

    def mark_complete(self):
        """Mark sync as complete and record end time."""
        self.end_time = time.time()

    def generate_report(self) -> str:
        """Generate a formatted report of sync statistics.

        Returns:
            Formatted statistics report
        """
        if not self.end_time:
            self.mark_complete()

        duration = self.end_time - self.start_time
        minutes = int(duration // 60)
        seconds = int(duration % 60)

        report = [
            "\n===== Sync Statistics =====",
            f"Duration: {minutes} minutes {seconds} seconds",
            f"Started: {datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "Document Processing:",
            f"  - Total documents found: {self.total_documents}",
            f"  - Documents processed: {self.documents_processed}",
            f"  - Documents skipped: {self.documents_skipped}",
            "",
            "Database Operations:",
            "  Chroma:",
            f"    - Insertions: {self.chroma_insertions}",
            f"    - Updates: {self.chroma_updates}",
            f"    - Deletions: {self.chroma_deletions}",
            "  Neo4j:",
            f"    - Nodes Created: {self.neo4j_nodes_created}",
            f"    - Relationships Created: {self.neo4j_relationships_created}",
            f"    - Deletions: {self.neo4j_deletions}",
            "",
            "Chunking:",
            f"  - Documents using LLM chunking: {self.llm_chunked_docs}",
            f"  - Documents using token-based: {self.token_chunked_docs}",
            f"  - Total LLM chunks created: {self.llm_chunks_created}",
            f"  - Total token-based chunks created: {self.token_chunks_created}",
            "",
            "Rate Limiting:",
            f"  - Number of rate limit hits: {self.rate_limit_hits}",
            f"  - Total wait time: {self.rate_limit_wait_time:.1f} seconds",
        ]

        return "\n".join(report)
