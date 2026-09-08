"""
xNFT - Antenna Measurement Software

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University
"""

import logging
import logging.config
import sys
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path

import yaml

logging.getLogger(__name__).addHandler(logging.NullHandler())

__version__ = version("xnft")


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
