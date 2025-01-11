import argparse
import logging
import os
import sys
from datetime import datetime

import chromadb
import requests
from chromadb.config import Settings
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

load_dotenv()


NOTION_API_TOKEN = os.environ.get("NOTION_API_TOKEN")


def get_page_content(api_token, page_id):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
    headers = {"Authorization": f"Bearer {api_token}", "Notion-Version": "2022-06-28"}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to retrieve page content: {response.status_code}")
        logger.error(response.text)
        return None


def parse_rich_text(rich_text):

    return "".join([text.get("text", {}).get("content", "") for text in rich_text])


def print_block_content(block):
    if block.get("type") == "paragraph":
        paragraph = block.get("paragraph", {}).get("rich_text", [])
        paragraph_text = parse_rich_text(paragraph)
        logger.debug(f"Paragraph: {paragraph_text}")
        return paragraph_text

    elif block.get("type") == "heading_1":
        heading = block.get("heading_1", {}).get("rich_text", [])
        heading_text = f"# {parse_rich_text(heading)}"
        logger.debug(f"Heading 1: {heading_text}")
        return heading_text

    elif block.get("type") == "heading_2":
        heading = block.get("heading_2", {}).get("rich_text", [])
        heading_text = f"## {parse_rich_text(heading)}"
        logger.debug(f"Heading 2: {heading_text}")
        return heading_text

    elif block.get("type") == "heading_3":
        heading = block.get("heading_3", {}).get("rich_text", [])
        heading_text = f"### {parse_rich_text(heading)}"
        logger.debug(f"Heading 3: {heading_text}")
        return heading_text

    elif block.get("type") == "bulleted_list_item":
        bullet = block.get("bulleted_list_item", {}).get("rich_text", [])
        bullet_text = f"* {parse_rich_text(bullet)}"
        logger.debug(f"Bulleted List Item: {bullet_text}")
        return bullet_text

    elif block.get("type") == "numbered_list_item":
        bullet = block.get("numbered_list_item", {}).get("rich_text", [])
        bullet_text = f"* {parse_rich_text(bullet)}"
        logger.debug(f"Numbered List Item: {bullet_text}")
        return bullet_text

    elif block.get("type") == "divider":
        divider = block.get("divider", {}).get("rich_text", [])
        divider = "---"
        logger.debug(f"Divider: {divider}")
        return divider

    else:
        logger.info(f"Block type not supported: {block.get('type')}")
        return ""


def initialize_chroma_client():

    chroma_client = chromadb.HttpClient(
        settings=Settings(
            anonymized_telemetry=False,
            chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
            chroma_client_auth_credentials=os.environ.get("CHROMA_AUTH_TOKEN"),
        ),
        host=os.environ.get("CHROMA_HOST"),
        port="443",
        ssl=True,
    )
    chroma_client.heartbeat()

    chroma_client.get_or_create_collection("langchain")
    embeddings = OllamaEmbeddings(
        base_url=f"https://{os.environ.get('OLLAMA_URL')}", model="nomic-embed-text"
    )
    vector_store = Chroma(
        client=chroma_client,
        collection_name="langchain",
        embedding_function=embeddings,
    )
    return vector_store


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Notion to Chroma sync script")
    parser.add_argument(
        "--clear-database",
        action="store_true",
        help="Clear the database before running the script",
    )

    args = parser.parse_args()

    if args.clear_database:
        logger.info("Clearing the database...")
        vector_store = initialize_chroma_client()
        vector_store.delete_collection()
        logger.info("Database cleared.")
        sys.exit()

    url = f"https://api.notion.com/v1/search/"

    headers = {
        "Authorization": f"Bearer {NOTION_API_TOKEN}",
        "Notion-Version": "2022-06-28",
    }
    data = {
        "query": "",
        "filter": {"value": "page", "property": "object"},
        "sort": {"direction": "ascending", "timestamp": "last_edited_time"},
    }
    response = requests.post(url, headers=headers, data=data)
    print(NOTION_API_TOKEN)
    if response.status_code != 200:
        logger.error(f"Failed to load page list: {response.status_code}")
        logger.error(response.text)
        raise Exception("Failed to retrieve page list")

    vector_store = initialize_chroma_client()

    results = vector_store.get()
    count = len(results["documents"])
    logger.info(f"Chroma document count: {count}")

    for notion_doc in response.json().get("results", []):

        notion_id = notion_doc.get("id")
        results = vector_store.get(ids=notion_id)
        count = len(results["documents"])
        logger.info(f"Chroma document count matching NotionID: {count}")

        content = get_page_content(NOTION_API_TOKEN, notion_id)

        try:
            title = (
                notion_doc.get("properties", {})
                .get("title", {})
                .get("title", [])[0]
                .get("plain_text", "Untitled")
            )
            logger.info(f"Title: {title}")
        except:
            logger.info("Title not found, using 'Untitled'")
            title = "Untitled"

        markdown_content = ""
        if content:
            for block in content.get("results", []):
                markdown_content += print_block_content(block) + "\n"
        markdown_content = markdown_content.strip()
        if len(markdown_content) == 0:
            vector_store.delete(ids=[notion_id])
            logger.warning(
                f"Removing empty document from Chroma: ID: {notion_id}, Title: {title}"
            )
            continue
            # TODO: And remove from database if it exists

        if count > 1:
            raise Exception(
                "Multiple documents with the same Notion ID found in Chroma. Exiting."
            )

        if count == 0:
            logger.info("Document does not exist in Chroma, preparing to insert...")
            document = Document(
                page_content=markdown_content,
                metadata={"title": title, "last_updated": str(datetime.now())},
                id=notion_id,
            )

            vector_store.add_documents([document])

            logger.info("Chroma document has been added.")
        else:
            logger.info("Document exists in Chroma. Checking for updates in notion...")
            document = results["documents"][0]

            last_updated = results["metadatas"][0]["last_updated"]

            notion_last_updated = datetime.strptime(
                notion_doc.get("last_edited_time"), "%Y-%m-%dT%H:%M:%S.%fZ"
            )
            chroma_last_updated = datetime.strptime(
                last_updated, "%Y-%m-%d %H:%M:%S.%f"
            )

            logger.info(f"Last updated in Chroma: {last_updated}")
            logger.info(f"Last updated in Notion: {notion_last_updated}")

            if chroma_last_updated < notion_last_updated:
                logger.info("Notion document has been updated.")
                document = Document(
                    page_content=markdown_content,
                    metadata={
                        "title": title,
                        "last_updated": str(datetime.now()),
                    },
                    id=notion_id,
                )
                logger.info("Updating Chroma document...")
                vector_store.update_document(document_id=notion_id, document=document)
                logger.info("Chroma document has been updated.")
            else:
                logger.info("Chroma document is up to date.")

    results = vector_store.get()
    count = len(results["documents"])
    logger.info(f"Chroma document count: {count}")
