"""
Handle loading of data files.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import logging
from pathlib import Path
from ...core.enums import FieldType, DataSourceType, DataPolarizationType
from ...core.types import FileInfo
from typing import List

logger = logging.getLogger(__name__)


class FieldLoaderRegistry:
    """
    File loader registry class to handle addition of new data loaders dynamically.
    """

    def __init__(self):
        # Dict to store loader functions into
        self._loaders = {}

    def loader_key(self, source, field, extension):
        """Generate a key for the _loaders list."""
        return (source, field, extension)

    def register(
        self,
        source: DataSourceType,
        field: FieldType,
        data_polarization: DataPolarizationType,
        extension: str,
        has_sp: bool = False,
    ):
        """
        Decorator to register a loader function for a given source and field
        type.

        Generates a key based on measurements source, field type, and file
        extension, then assigns the value to the loader function.

        Parameters
        ----------
        source : DataSourceType
            System type that generated the data (e.g., HFSS, NSI, etc.).
        field : FieldType
            Field type of measurement.
            - FieldType.NEAR : Near-field measurement.
            - FieldType.FAR : Far-field measurement.
        data_polarization : DataPolarizationType
            - DataPolarizationType.SINGLE_POL : Single polarization per file
            - DataPolarizationType.COMBO_POL : Combined polarization in file
        extension : str
            File extension (e.g., .csv, .nfd, .ffd, etc.).
        has_sp : bool, optional
            File has s-parameters to select from, by default False
        """

        def decorator(func):
            # Generate entry in loader dicionary
            self._loaders[self.loader_key(source=source, field=field, extension=extension)] = func

            # Add declared attributes of the loader
            func.__attributes__ = {
                "source": source,
                "field": field,
                "extension": extension,
                "data_polarization": data_polarization,
                "has_sp": has_sp,
            }

            return func

        return decorator

    def load(
        self,
        source: DataSourceType,
        field: FieldType,
        file_list: List[FileInfo],
    ):
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
        file_list : List[FileInfo]
            List of FileInfo objects containing files and measurement information.
        """
        logger.debug(f'{file_list}')
        extension = Path(file_list[0].path).suffix

        # Check all files exist and extensions are the same
        for file in file_list:
            file_path = Path(file.path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {str(file_path)}")
            if file_path.suffix != extension:
                raise TypeError("All file extensions must be of the same type.")

        loader_function = self.get_loader(source, field, extension)

        return_value = loader_function(file_list)

        return return_value

    def get_loader(self, source, field, extension):
        loader_key = self.loader_key(source=source, field=field, extension=extension)
        logger.debug("Available loaders: %s", self._loaders)

        try:
            loader_function = self._loaders[loader_key]
        except KeyError as exc:
            raise NotImplementedError(
                f"No file loader exists for: "
                f"{{ source: '{source.value}', field: '{field.value}',"
                f" extension: '{extension}' }} ({loader_key}). "
                f"Available options are {self._loaders}. {exc}"
            ) from exc
        return loader_function


field_loader_registry = FieldLoaderRegistry()
