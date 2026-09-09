"""
Provides registry for extensions, e.g., loaders, algorithms, reports, etc.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import logging
from abc import ABC
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..common.enums import DataPolarizationType, DataSourceType, FieldType, ScanType
from ..common.types import FileInfo

logger = logging.getLogger(__name__)

# Declare registry type helpers
LoaderFunction = Callable[[list[FileInfo]], Any]
FieldLoaderKey = tuple[DataSourceType, FieldType, str]


class BaseRegistry(ABC):
    def __len__(self) -> int:
        """Return number of registered objects."""
        raise NotImplementedError

    def clear(self) -> None:
        """Removes all registered objects."""
        raise NotImplementedError

    def items(self):
        """Returns registered items."""
        raise NotImplementedError

    def values(self):
        """Returns registered functions."""
        raise NotImplementedError


class FieldLoaderRegistry(BaseRegistry):
    """
    File loader registry class to handle addition of new data loaders dynamically.
    """

    def __init__(self) -> None:
        # Dict to store loader functions into
        self._loaders: dict[FieldLoaderKey, LoaderFunction] = {}

    # --- Override BaseRegistry Behavior ---

    def __len__(self) -> int:
        return len(self._loaders)

    def clear(self) -> None:
        self._loaders.clear()

    def items(self):
        return self._loaders.items()

    def values(self):
        return self._loaders.values()

    # --- Loader Functions ---

    def loader_key(self, source, field, extension):
        """Generate a key for the field-loader registry."""
        return (source, field, extension.strip().casefold())

    def register(
        self,
        source: DataSourceType,
        data_polarization: DataPolarizationType,
        extension: str,
        field: FieldType = FieldType.NEAR,
        scan: ScanType = ScanType.PLANAR,
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
        data_polarization : DataPolarizationType
            - DataPolarizationType.SINGLE_POL : Single polarization per file
            - DataPolarizationType.COMBO_POL : Combined polarization in file
        extension : str
            File extension (e.g., .csv, .nfd, .ffd, etc.).
        field : FieldType
            Field type of measurement.
            - FieldType.NEAR : Near-field measurement
            - FieldType.FAR : Far-field measurement
        scan : ScanType
            Scan type of measurement.
            - ScanType.PLANAR : Planar measurement coordinates
            - ScanType.CYLINDRICAL : Cylindrical measurement coordinates
            - ScanType.SPHERICAL : Spherical measurement coordinates
        has_sp : bool, optional
            File has s-parameters to select from, by default False
        """

        def decorator(func):
            # Generate entry in loader dicionary
            key = self.loader_key(source=source, field=field, extension=extension)
            self._loaders[key] = func

            # Add declared attributes of the loader
            func.__attributes__ = {
                "source": source,
                "field": field,
                "scan": scan,
                "extension": extension,
                "data_polarization": data_polarization,
                "has_sp": has_sp,
            }

            logger.debug(
                "Registered field loader %s for key %r",
                func.__qualname__,
                key,
            )

            return func

        return decorator

    def load(
        self,
        source: DataSourceType,
        field: FieldType,
        file_list: list[FileInfo],
    ):
        """
        Load a field file using appropriate loader.

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
        if not file_list:
            raise ValueError("At least one file is required.")

        logger.debug("Loading field files: %s", file_list)

        extension = Path(file_list[0].path).suffix.strip().casefold()

        # Check all files exist and extensions are the same
        for file in file_list:
            file_path = Path(file.path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path!s}")
            if file_path.suffix.strip().casefold() != extension:
                raise TypeError("All file extensions must be of the same type.")

        loader = self.get_loader(source, field, extension)

        return loader(file_list)

    def get_loader(
        self,
        source: DataSourceType,
        field: FieldType,
        extension: str,
    ):
        """Get loader for the specified data format.

        Parameters
        ----------
        source : DataSourceType
            Source type of the field data.
        field : FieldType
            Type of the field data (e.g., NEAR or FAR).
        extension : str
            File extension of the field data.

        Returns
        -------
        LoaderFunction
            Registered loader function

        Raises
        ------
        NotImplementedError
            If no matching loader is registered.
        """
        loader_key = self.loader_key(source=source, field=field, extension=extension)
        logger.debug("Available field loaders: %s", self._loaders)

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


class AlgorithmRegistry(BaseRegistry):
    pass


class ReportRegistry(BaseRegistry):
    pass


class LoaderRegistry:
    """Container class for loader registries."""

    def __init__(self) -> None:
        self.fields = FieldLoaderRegistry()

        # TODO: Implement further registries
        # self.probes = ProbeLoaderRegistry()
        # self.gain = GainLoaderRegistry()


class Registry:
    def __init__(self):
        self.loaders = LoaderRegistry()
        self.algorithms = AlgorithmRegistry()
        self.reports = ReportRegistry()


registry = Registry()
