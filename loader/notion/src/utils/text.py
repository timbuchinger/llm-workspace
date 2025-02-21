import re

import tiktoken


class TextProcessor:
    @staticmethod
    def split_text(text: str, max_tokens: int = 300, overlap: int = 50) -> list[str]:
        """Split text into chunks based on token count with overlap."""
        tokenizer = tiktoken.get_encoding("cl100k_base")
        tokens = tokenizer.encode(text)
        chunks = []
        for i in range(0, len(tokens), max_tokens - overlap):
            chunk = tokens[i : i + max_tokens]
            chunks.append(tokenizer.decode(chunk))
        return chunks

    @staticmethod
    def clean_markdown(content: str) -> str:
        """Clean and format markdown content."""
        # Remove empty content
        if not content:
            return ""

        # Strip whitespace
        content = content.strip()

        # Replace multiple newlines with double newline
        content = re.sub(r"\n{3,}", "\n\n", content)

        return content
