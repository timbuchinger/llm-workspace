import logging
import os
from pathlib import Path
from typing import Optional

import yaml


def load_yaml_config(config_path: str) -> dict:
    """Load logging configuration from YAML file.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Dictionary containing logging configuration
    """
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return None


def configure_logger(name: str, config: dict) -> None:
    """Configure a specific logger based on YAML configuration.

    Args:
        name: Logger name
        config: Configuration dictionary from YAML
    """
    logger = logging.getLogger(name)

    # Set default level if specified
    if config.get("defaults", {}).get("level"):
        logger.setLevel(config["defaults"]["level"])

    # Apply specific logger configuration if it exists
    if name in config.get("loggers", {}):
        logger_config = config["loggers"][name]
        if "level" in logger_config:
            logger.setLevel(logger_config["level"])


def setup_logging(
    config_path: Optional[str] = None, level: Optional[str] = None
) -> None:
    """Setup logging configuration for the application.

    Args:
        config_path: Optional path to YAML configuration file
        level: Optional logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               If not provided and no config file exists, defaults to INFO
    """
    # First try to load YAML config
    config = None
    if config_path:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), config_path
        )
        config = load_yaml_config(config_path)

    if config:
        # Configure root logger with handlers and formatters
        formatter = logging.Formatter(
            config.get("formatters", {})
            .get("standard", {})
            .get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(config.get("defaults", {}).get("level", "INFO"))

        # Configure specific loggers
        for logger_name in config.get("loggers", {}):
            configure_logger(logger_name, config)
    else:
        # Fallback to basic configuration if no YAML config
        if level is None:
            level = "INFO"

        logging.basicConfig(
            level=getattr(logging, level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name.

    Args:
        name: Name for the logger, typically __name__ of the module

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
