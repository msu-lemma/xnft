"""
xNFT - Antenna Measurement Software

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University
"""

import sys
import logging
import logging.config
import yaml
from pathlib import Path
from importlib.resources import files
from importlib.metadata import version


logging.getLogger(__name__).addHandler(logging.NullHandler())

__version__ = version("xnft")


# def configure_logging(config_name: str = "logging.dev.yaml") -> None:
#     try:
#         config_path = files("xnft.resources") / config_name
#         with config_path.open("r", encoding="utf-8") as f:
#             config_dict = yaml.safe_load(f)
#         logging.config.dictConfig(config_dict)

#         for logger in logging.root.manager.loggerDict.values():
#             if hasattr(logger, "propagate"):
#                 logger.propagate = True

#     except Exception:
#         logging.basicConfig(level=logging.INFO)
#         logging.getLogger(__name__).exception("Logging configuration failed; using fallback")
def configure_logging(config_name="logging.all.yaml"):

    # Load base config
    config_path = files("xnft.resources") / config_name
    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if getattr(sys, "frozen", False):
        log_dir = Path.home() / ".xnft"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "xnft.log"

        config["handlers"]["file"] = {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "filename": str(log_file),
            "formatter": "dev",
            "encoding": "utf-8",
        }

        config["root"]["handlers"].append("file")

    logging.config.dictConfig(config)


configure_logging()
