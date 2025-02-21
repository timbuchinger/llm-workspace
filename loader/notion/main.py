#!/usr/bin/env python3
import argparse
import logging
import os
import sys

from dotenv import load_dotenv
from src.api.notion import NotionAPI
from src.storage.chroma import ChromaStore
from src.sync import NotionSync
from src.utils.logging import setup_logging

logger = setup_logging()


def main():
    """Main entry point for the Notion to Chroma sync tool."""
    parser = argparse.ArgumentParser(description="Notion to Chroma sync script")
    parser.add_argument(
        "--clear-database",
        action="store_true",
        help="Clear the database before running the script",
    )

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()
    notion_token = os.environ.get("NOTION_API_TOKEN")
    if not notion_token:
        logger.error("NOTION_API_TOKEN environment variable is required")
        sys.exit(1)

    # Initialize components
    chroma_store = ChromaStore()

    if args.clear_database:
        logger.info("Clearing the database...")
        chroma_store.clear_collection()
        logger.info("Database cleared.")
        sys.exit(0)

    notion_api = NotionAPI(notion_token)
    sync = NotionSync(notion_api, chroma_store)

    # Run sync
    try:
        sync.sync()
    except Exception as e:
        logger.error(f"Sync failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
