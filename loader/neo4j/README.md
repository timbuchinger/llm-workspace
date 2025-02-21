# Notion to ChromaDB/Neo4j Sync

A tool for synchronizing Notion pages to ChromaDB and Neo4j, with relationship extraction using LLMs.

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd loader/memgraph
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package in development mode:
```bash
pip install -e .
```

## Configuration

1. Copy the example environment file:
```bash
cp .env_example .env
```

2. Edit .env and fill in your configuration:
```
NOTION_API_TOKEN=your_notion_token
CHROMA_AUTH_TOKEN=your_chroma_token
CHROMA_HOST=your_chroma_host
CHROMA_COLLECTION=notion
OLLAMA_HOST=your_ollama_host
NEO4J_URI=your_neo4j_uri
NEO4J_USER=your_neo4j_user
NEO4J_PASSWORD=your_neo4j_password
NEO4J_DATABASE=notion

# Optional: Path to logging configuration file
LOG_CONFIG_PATH=logging.yaml
```

### Logging Configuration

The tool supports granular logging control through a YAML configuration file. By default, it looks for `logging.yaml` in the project root, but you can specify a different path using the `LOG_CONFIG_PATH` environment variable.

Example logging.yaml:
```yaml
version: 1
disable_existing_loggers: false

defaults:
  level: INFO

loggers:
  src.storage.neo4j:
    level: WARNING
  src.llm.chunker:
    level: DEBUG
  src.llm.extractor:
    level: INFO
  src.storage.chroma:
    level: INFO
  src.api.notion:
    level: INFO

handlers:
  console:
    class: logging.StreamHandler
    formatter: standard
    stream: ext://sys.stdout

formatters:
  standard:
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

This allows you to:
- Set different logging levels per module
- Configure logging format
- Override the default logging level
- Control handler configuration

## Usage

The recommended way to run the sync tool is using the module directly. The old `app.py` script is deprecated and will be removed in a future version.

### 1. Recommended: Running the module directly

You can run the module directly using Python:

```bash
# From the loader/memgraph directory
python -m src.main

# With debug logging
python -m src.main --log-level DEBUG

# Clear databases
python -m src.main --clear-database
```

This method provides proper stats tracking, better error handling, and improved code organization.

### 2. Alternative: Using the CLI command (if installed as package)

If you've installed the package using `pip install -e .`, you can also use the `notion-sync` command:

```bash
notion-sync [--log-level DEBUG] [--clear-database]
```

However, running the module directly (method 1) is the recommended approach as it ensures you're using the latest version with all features like proper stats tracking.

## Features

- Syncs Notion pages to ChromaDB for vector search
- Creates a graph representation in Neo4j
- Extracts relationships using LLMs
- Supports incremental updates
- Skip functionality with #skip tag
- Configurable logging levels

## Architecture

The package is organized into several modules:

- `api/`: Notion API integration
- `llm/`: Language model integration and relationship extraction
- `storage/`: ChromaDB and Neo4j storage implementations
- `utils/`: Common utilities and helpers
- `sync.py`: Main synchronization logic
- `config.py`: Configuration management

## Requirements

- Python 3.8+
- Neo4j Database
- ChromaDB instance
- Notion API access
- LLM provider (Ollama, Gemini, or Groq)
