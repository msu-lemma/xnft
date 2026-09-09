"""
Provides registry for extensions, e.g., loaders, algorithms, reports, etc.

Copyright 2025-2026 LEmmA, Electromagnetics Research Group, Michigan State University.
"""

import logging
from abc import ABC
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..common.enums import DataPolarizationType, FieldType, ScanType
from ..common.types import DataSource, FileInfo

logger = logging.getLogger(__name__)

# Declare registry type helpers
LoaderFunction = Callable[..., Any]
FieldLoaderKey = tuple[DataSource, FieldType, str]


@dataclass(frozen=True, slots=True)
class LoaderMetadata:
    source: DataSource
    data_polarization: DataPolarizationType
    extension: str
    field: FieldType
    scan_type: ScanType
    has_sp: bool


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


class DataSourceRegistry(BaseRegistry):
    """Handles mapping between source ID and display name."""

    def __init__(self) -> None:
        self._sources: dict[str, DataSource] = {}

    def register(
        self,
        id: str,
        display_name: str,
    ) -> DataSource:

        source = DataSource(id=id, display_name=display_name)

        if source.id in self._sources and source != self._sources.get(source.id):
            raise ValueError(f"DataSource {source.id!r} already registered.")

        self._sources[source.id] = source

        logger.debug("Registered DataSource %s (%s)", source.id, source.display_name)

        return source

    def get(self, source_id: str) -> DataSource:
        return self._sources[source_id]


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

    def loader_key(self, source, field_type, scan_type, extension):
        """Generate a key for the field-loader registry."""
        return (source, field_type, scan_type, extension.strip().casefold())

    def register(
        self,
        source: DataSource,
        data_polarization: DataPolarizationType,
        extension: str,
        field: FieldType = FieldType.NEAR,
        scan_type: ScanType = ScanType.PLANAR,
        has_sp: bool = False,
    ):
        """
        Decorator to register a loader function for a given source and field
        type.

        Generates a key based on measurements source, field type, and file
        extension, then assigns the value to the loader function.

        Parameters
        ----------
        source : DataSourceDefinition
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
        scan_type : ScanType
            Scan type of measurement.
            - ScanType.PLANAR : Planar measurement coordinates
            - ScanType.CYLINDRICAL : Cylindrical measurement coordinates
            - ScanType.SPHERICAL : Spherical measurement coordinates
        has_sp : bool, optional
            File has s-parameters to select from, by default False
        """
        extension = extension.strip().casefold()

        if not extension.startswith("."):
            raise ValueError("Loader extension must start with '.'")

        # Store metadata on the loader for parsing by consumers
        metadata = LoaderMetadata(
            source=source,
            data_polarization=data_polarization,
            extension=extension,
            field=field,
            scan_type=scan_type,
            has_sp=has_sp,
        )

        def decorator(func: LoaderFunction) -> LoaderFunction:
            # Generate entry in loader dicionary
            key = self.loader_key(
                source=source,
                field_type=field,
                scan_type=scan_type,
                extension=extension,
            )

            if key in self._loaders:
                current = self._loaders[key]
                raise ValueError(
                    f"Loader {key!r} already registered by {current.__module__}.{current.__qualname__}. Cannot register {func.__module__}.{func.__qualname__}."
                )

            self._loaders[key] = func

            # Add declared attributes of the loader
            func.__loader_metadata__ = metadata

            logger.debug(
                "Registered field loader %s for key %r",
                func.__qualname__,
                key,
            )

            return func

        return decorator

    def load(
        self,
        source: DataSource,
        field_type: FieldType,
        scan_type: ScanType,
        file_list: list[FileInfo],
    ):
        """
        Load a field file using appropriate loader.

        Parameters
        ----------
        source : DataSource
            System type that generated the data (e.g., HFSS, NSI, etc.).
        field_type : FieldType
            Field type of measurement.
            - FieldType.NEAR : Near-field measurement.
            - FieldType.FAR : Far-field measurement.
        scan_type : ScanType
            Scan type of measurement.
            - ScanType.PLANAR : Planar measurement coordinates
            - ScanType.CYLINDRICAL : Cylindrical measurement coordinates
            - ScanType.SPHERICAL : Spherical measurement coordinates
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

        loader = self.get_loader(
            source=source,
            field_type=field_type,
            scan_type=scan_type,
            extension=extension,
        )

        return loader(file_list)

    def get_loader(
        self,
        source: DataSource,
        field_type: FieldType,
        scan_type: ScanType,
        extension: str,
    ):
        """Get loader for the specified data format.

        Parameters
        ----------
        source : DataSourceDefinition
            Source type of the field data.
        field_type : FieldType
            Type of the field data (e.g., NEAR or FAR).
        scan_type : ScanType
            Scan type of measurement.
            - ScanType.PLANAR : Planar measurement coordinates
            - ScanType.CYLINDRICAL : Cylindrical measurement coordinates
            - ScanType.SPHERICAL : Spherical measurement coordinates
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
        loader_key = self.loader_key(
            source=source,
            field_type=field_type,
            scan_type=scan_type,
            extension=extension,
        )
        logger.debug("Available field loaders: %s", self._loaders)

        try:
            loader_function = self._loaders[loader_key]
        except KeyError as e:
            raise NotImplementedError(
                f"No file loader exists for: {{ {source=}, {field_type=}, "
                f"{scan_type=}, {extension=} }} . Available options are "
                f"{self._loaders}. {e}"
            ) from e
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
        self.data_sources = DataSourceRegistry()
        self.loaders = LoaderRegistry()
        self.algorithms = AlgorithmRegistry()
        self.reports = ReportRegistry()


registry = Registry()
