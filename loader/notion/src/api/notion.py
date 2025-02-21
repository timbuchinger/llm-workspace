import logging
from datetime import datetime
from typing import Dict, Optional

import requests

from ..utils.logging import setup_logging

logger = setup_logging()


class NotionAPI:
    """Handles all interactions with the Notion API."""

    def __init__(self, api_token: str):
        """Initialize the Notion API client.

        Args:
            api_token: Notion API authentication token
        """
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Notion-Version": "2022-06-28",
        }

    def get_page_content(self, page_id: str) -> Optional[Dict]:
        """Retrieve content of a specific page from Notion.

        Args:
            page_id: The ID of the Notion page

        Returns:
            Dict containing page content or None if request fails
        """
        url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()

        logger.error(f"Failed to retrieve page content: {response.status_code}")
        logger.error(response.text)
        return None

    def search_pages(self) -> Optional[Dict]:
        """Search for all pages in the Notion workspace.

        Returns:
            Dict containing search results or None if request fails
        """
        url = "https://api.notion.com/v1/search/"
        data = {
            "query": "",
            "filter": {"value": "page", "property": "object"},
            "sort": {"direction": "ascending", "date": "last_edited_time"},
        }

        response = requests.post(url, headers=self.headers, json=data)

        if response.status_code == 200:
            return response.json()

        logger.error(f"Failed to load page list: {response.status_code}")
        logger.error(response.text)
        return None

    def get_page_metadata(self, page: Dict) -> Dict[str, str]:
        """Extract metadata from a Notion page.

        Args:
            page: Dict containing page data from Notion API

        Returns:
            Dict containing extracted metadata (title and last_edited_time)
        """
        try:
            title = (
                page.get("properties", {})
                .get("title", {})
                .get("title", [])[0]
                .get("plain_text", "Untitled")
            )
        except:
            logger.info("Title not found, using 'Untitled'")
            title = "Untitled"

        last_edited_time = datetime.strptime(
            page.get("last_edited_time"), "%Y-%m-%dT%H:%M:%S.%fZ"
        )

        return {
            "title": title,
            "last_edited_time": last_edited_time,
        }
