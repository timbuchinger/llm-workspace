import logging
from typing import Dict, List, Optional

from ..utils.logging import setup_logging

logger = setup_logging()


class BlockTypes:
    """Constants for Notion block types."""

    PARAGRAPH = "paragraph"
    HEADING_1 = "heading_1"
    HEADING_2 = "heading_2"
    HEADING_3 = "heading_3"
    BULLETED_LIST = "bulleted_list_item"
    NUMBERED_LIST = "numbered_list_item"
    DIVIDER = "divider"


class BlockParser:
    """Parser for Notion block content."""

    @staticmethod
    def parse_rich_text(rich_text: List[Dict]) -> str:
        """Parse rich text content from Notion blocks.

        Args:
            rich_text: List of rich text objects from Notion API

        Returns:
            Concatenated plain text content
        """
        return "".join([text.get("text", {}).get("content", "") for text in rich_text])

    def parse_block(self, block: Dict) -> Optional[str]:
        """Parse a Notion block into markdown format.

        Args:
            block: Dict containing block data from Notion API

        Returns:
            Markdown formatted string or None if block type not supported
        """
        block_type = block.get("type")
        parser_method = self._get_parser_method(block_type)

        if parser_method:
            return parser_method(block)

        logger.info(f"Block type not supported: {block_type}")
        return None

    def _get_parser_method(self, block_type: str):
        """Get the appropriate parser method for a block type.

        Args:
            block_type: Type of the Notion block

        Returns:
            Parser method or None if type not supported
        """
        parsers = {
            BlockTypes.PARAGRAPH: self._parse_paragraph,
            BlockTypes.HEADING_1: lambda b: self._parse_heading(b, "heading_1", "#"),
            BlockTypes.HEADING_2: lambda b: self._parse_heading(b, "heading_2", "##"),
            BlockTypes.HEADING_3: lambda b: self._parse_heading(b, "heading_3", "###"),
            BlockTypes.BULLETED_LIST: self._parse_bulleted_list,
            BlockTypes.NUMBERED_LIST: self._parse_numbered_list,
            BlockTypes.DIVIDER: self._parse_divider,
        }
        return parsers.get(block_type)

    def _parse_paragraph(self, block: Dict) -> str:
        """Parse paragraph block.

        Args:
            block: Paragraph block data

        Returns:
            Parsed paragraph text
        """
        paragraph = block.get(BlockTypes.PARAGRAPH, {}).get("rich_text", [])
        paragraph_text = self.parse_rich_text(paragraph)
        logger.debug(f"Paragraph: {paragraph_text}")
        return paragraph_text

    def _parse_heading(
        self, block: Dict, heading_type: str, markdown_prefix: str
    ) -> str:
        """Parse heading block.

        Args:
            block: Heading block data
            heading_type: Type of heading (heading_1, heading_2, heading_3)
            markdown_prefix: Markdown syntax for heading level (#, ##, ###)

        Returns:
            Parsed heading text with markdown formatting
        """
        heading = block.get(heading_type, {}).get("rich_text", [])
        heading_text = f"{markdown_prefix} {self.parse_rich_text(heading)}"
        logger.debug(f"Heading: {heading_text}")
        return heading_text

    def _parse_bulleted_list(self, block: Dict) -> str:
        """Parse bulleted list item block.

        Args:
            block: Bulleted list item block data

        Returns:
            Parsed list item with bullet point
        """
        bullet = block.get(BlockTypes.BULLETED_LIST, {}).get("rich_text", [])
        bullet_text = f"* {self.parse_rich_text(bullet)}"
        logger.debug(f"Bulleted List Item: {bullet_text}")
        return bullet_text

    def _parse_numbered_list(self, block: Dict) -> str:
        """Parse numbered list item block.

        Args:
            block: Numbered list item block data

        Returns:
            Parsed list item with bullet point
        """
        bullet = block.get(BlockTypes.NUMBERED_LIST, {}).get("rich_text", [])
        bullet_text = f"* {self.parse_rich_text(bullet)}"
        logger.debug(f"Numbered List Item: {bullet_text}")
        return bullet_text

    def _parse_divider(self, block: Dict) -> str:
        """Parse divider block.

        Args:
            block: Divider block data

        Returns:
            Markdown divider
        """
        logger.debug("Divider")
        return "---"
