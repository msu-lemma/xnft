"""
Handle loading of data files.

Copyright 2025-2026 The LEmmA Group, Michigan State University.
"""

from typing import Literal
import logging
from pathlib import Path
from collections import defaultdict
from ..core.types import FieldType, DataSourceType

logger = logging.getLogger(__name__)


class FileLoaderRegistry:
    """
    File loader registry class to handle various file types.
    """

    def __init__(self):
        self._loaders = {}

    def loader_key(self, source, field, extension):
        """Generate a key for the _loaders list."""
        return (source, field, extension)

    def register(
        self,
        source: DataSourceType,
        field: FieldType,
        extension: str,
    ):
        """
        Decorator to register a loader function for a given source and field
        type.

        Parameters
        ----------
        source : DataSourceType
            System type that generated the data (e.g., HFSS, NSI, etc.).
        field : FieldType
            Field type of measurement.
            - FieldType.NEAR : Near-field measurement.
            - FieldType.FAR : Far-field measurement.
        extension : str
            File extension (e.g., .csv, .nfd, .ffd, etc.).
        """

        def decorator(func):
            self._loaders[
                self.loader_key(
                    source=source, field=field, extension=extension
                )
            ] = func
            return func

        return decorator

    def load(self, source: DataSourceType, field: FieldType, path: str):
        """
        Load a file using appropriate loader.

        Parameters
        ----------
        source : DataSourceType
            System type that generated the data (e.g., HFSS, NSI, etc.).
        field : FieldType
            Field type of measurement.
            - FieldType.NEAR : Near-field measurement.
            - FieldType.FAR : Far-field measurement.
        path : str
            String representing the path to a file.
        """
        extension = Path(path).suffix
        loader_key = self.loader_key(
            source=source, field=field, extension=extension
        )

        # with open(path, "r", encoding="utf-8") as f:
        logger.debug("Available loaders: %s", self._loaders)

        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {str(file_path)}")

        try:
            loader_function = self._loaders[loader_key]
        except KeyError as exc:
            raise NotImplementedError(
                f"No file loader exists for: "
                f"{{ source: '{source.value}', field: '{field.value}',"
                f" extension: '{extension}' }} ({loader_key}). "
                f"Available options are {self._loaders}. {exc}"
            ) from exc

        return_value = loader_function(file_path)

        return return_value

    @property
    def loaders(self):
        """
        Return dictionary of field type, source type and accepted file
        extensions.
        """
        loader_dict = {
            FieldType.NEAR: defaultdict(list),
            FieldType.FAR: defaultdict(list),
        }

        for key in self._loaders.keys():
            source, field, extension = key
            loader_dict[field][source].append(extension)

        return loader_dict


registry = FileLoaderRegistry()
