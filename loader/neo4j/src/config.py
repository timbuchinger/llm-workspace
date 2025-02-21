import os
from typing import Dict

from dotenv import load_dotenv

load_dotenv()


class Config:
    # Model provider configuration
    MODEL_PROVIDER = "groq"  # Options: "ollama", "gemini", "groq"

    # Configuration paths
    LOG_CONFIG_PATH = "logging.yaml"

    # Required environment variables
    REQUIRED_ENV_VARS: Dict[str, str] = {
        "NOTION_API_TOKEN": os.environ.get("NOTION_API_TOKEN"),
        "CHROMA_AUTH_TOKEN": os.environ.get("CHROMA_AUTH_TOKEN"),
        "CHROMA_HOST": os.environ.get("CHROMA_HOST"),
        "CHROMA_COLLECTION": os.environ.get("CHROMA_COLLECTION", "notion"),
        "OLLAMA_HOST": os.environ.get("OLLAMA_HOST"),
        "NEO4J_URI": os.environ.get("NEO4J_URI"),
        "NEO4J_USER": os.environ.get("NEO4J_USER"),
        "NEO4J_PASSWORD": os.environ.get("NEO4J_PASSWORD"),
        "NEO4J_DATABASE": os.environ.get("NEO4J_DATABASE", "notion"),
    }

    @classmethod
    def get_log_config_path(cls) -> str:
        """Get the logging configuration file path."""
        return os.environ.get("LOG_CONFIG_PATH", cls.LOG_CONFIG_PATH)

    @classmethod
    def validate_env(cls) -> None:
        """Validate that all required environment variables are set."""
        missing_vars = [
            var for var, value in cls.REQUIRED_ENV_VARS.items() if not value
        ]
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

    @classmethod
    def get_env(cls, key: str) -> str:
        """Get environment variable value."""
        return cls.REQUIRED_ENV_VARS[key]

    # Convenience properties for commonly used values
    @property
    def notion_token(self) -> str:
        return self.get_env("NOTION_API_TOKEN")

    @property
    def chroma_collection(self) -> str:
        return self.get_env("CHROMA_COLLECTION")

    @property
    def neo4j_database(self) -> str:
        return self.get_env("NEO4J_DATABASE")
