"""
Copyright 2025-2026
LEmmA, Electromagnetics Research Group, Michigan State University
"""

import logging
import logging.config
import yaml
from importlib.resources import files
from importlib.metadata import version

logging.getLogger(__name__).addHandler(logging.NullHandler())

__version__ = version("xnft")


def configure_logging(config_name: str = "logging.dev.yaml") -> None:
    try:
        config_path = files("xnft.resources") / config_name
        with config_path.open("r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)
        logging.config.dictConfig(config_dict)

        for logger in logging.root.manager.loggerDict.values():
            if hasattr(logger, "propagate"):
                logger.propagate = True

    except Exception:
        logging.basicConfig(level=logging.INFO)
        logging.getLogger(__name__).exception("Logging configuration failed; using fallback")


configure_logging()
