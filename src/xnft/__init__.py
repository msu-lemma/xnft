"""
Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

# Configure package logging
import logging
import logging.config
import yaml
from pathlib import Path


logging.getLogger(__name__).addHandler(logging.NullHandler())

# Set package version number
__version__ = "0.1.0"


def configure_logging(
    config_path: str = "resources/logging.dev.yaml"
):
    """
    Configure logging format.

    Parameters
    ----------
    config_path : _type_, optional
        _description_, by default None
    default_config : str, optional
        _description_, by default "logging.dev.yaml"
    """
    file_path = Path(__file__).resolve().parent
    # if False and config_path is not None:
    if config_path is not None:
        file_path = file_path / config_path
        with open(file_path, encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)
        logging.config.dictConfig(config_dict)


configure_logging()
