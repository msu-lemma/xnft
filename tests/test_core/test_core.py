"""Test file loaders."""

from collections import defaultdict
from pathlib import Path
from typing import Any

import pytest
import xarray as xr

from xnft.algorithms.planar_near_field_transform import planar_near_field_transform
from xnft.common.enums import (
    CoordinateSystemType,
    DataSourceType,
    FieldType,
    PolarizationType,
)
from xnft.common.registry import registry
from xnft.common.types import FileInfo
from xnft.loaders import register_builtin_loaders

test_dir = Path(__file__).parent.parent
test_dict = {
    "source": [DataSourceType.HFSS, DataSourceType.ANALYTIC, DataSourceType.LEMMA],
    "field": [FieldType.NEAR, FieldType.FAR],
}


def generate_tests(fields=test_dict["field"]):
    """
    Generate testing options for registry.load test.
    """
    # Populate file loader registry
    register_builtin_loaders()

    tests_list = []
    for source in test_dict["source"]:
        for field in fields:
            nf_test_dir = (
                test_dir
                / "data"
                / field.lower().replace(" ", "_")
                / source.name.lower()
            )

            test_file_dict = defaultdict(list)

            for path in nf_test_dir.glob("*"):
                if path.is_file() and path.name[0:3].isnumeric():
                    test_id = int(path.name[0:3])

                    polarization = {PolarizationType.CO_POL, PolarizationType.CROSS_POL}
                    if path.stem.split("_")[-1] == "co":
                        polarization = PolarizationType.CO_POL
                    elif path.stem.split("_")[-1] == "cx":
                        polarization = PolarizationType.CROSS_POL

                    file_info = FileInfo(path=path, polarization=polarization)
                    test_file_dict[test_id].append(file_info)

            for file_info_list in test_file_dict.values():
                tests_list.append((source, field, file_info_list))

    return tests_list


@pytest.fixture
def load_test_file(request: pytest.FixtureRequest):
    """
    Load file to test.
    """
    source, field, file_list = request.param
    result = registry.loaders.fields.load(source, field, file_list)
    return result, request.param


@pytest.mark.parametrize(
    "load_test_file",
    generate_tests(),
    ids=lambda c: f"{c[0]} {c[1]} {c[2][0].path.stem.split('_')[0]}",
    indirect=True,
)
def test_file_loader(load_test_file: tuple[Any, Any]):
    result, params = load_test_file
    try:
        assert isinstance(result, xr.Dataset)
    except AssertionError as e:
        raise AssertionError(f"Error processing test: {params} / {result}") from e


@pytest.mark.parametrize(
    "load_test_file",
    generate_tests(fields=[FieldType.NEAR]),
    ids=lambda c: f"{c[0]} {c[1]} {c[2][0].path.stem.split('_')[0]}",
    indirect=True,
)
def test_planar_near_field_transform(load_test_file: tuple[Any, Any]):
    # TODO/FIXME: Create _numerical_ accuracy test instead of just output type test
    source_field, params = load_test_file

    if source_field.attrs["coordinate_system"] == CoordinateSystemType.CARTESIAN:
        # Test single frequency transform
        result = planar_near_field_transform(
            near_field=source_field,
            probe_correction=None,
            frequencies=source_field.frequency.values[0],
        )
        try:
            assert isinstance(result, xr.Dataset)
        except AssertionError as e:
            raise AssertionError(
                f"Error processing single frequency test: {params} / {result}"
            ) from e

        # Test multi-frequency transform
        result = planar_near_field_transform(
            near_field=source_field,
            probe_correction=None,
            frequencies=source_field.frequency.values[
                :3
            ],  # pick the first 3 frequencies to keep tests quick
        )
        try:
            assert isinstance(result, xr.Dataset)
        except AssertionError as e:
            raise AssertionError(f"Error processing test: {params} / {result}") from e

    elif source_field.attrs["coordinate_system"] == CoordinateSystemType.SPHERICAL:
        # TODO: Insert spherical NFT here

        pass
