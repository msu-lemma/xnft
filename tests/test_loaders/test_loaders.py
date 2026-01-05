"""Test theory file loader."""

from pathlib import Path

import pytest

import xarray as xr

from xnft.loaders.file_registry import registry

test_dir = Path(__file__).parent.parent
test_dict = {
    "source": ["HFSS", "Theory"],
    "field": ["Near Field", "Far Field"],
}

hfss_field_extensions = {
    "Near Field": [".nfd", ".csv"],
    "Far Field": [".ffd", ".csv"],
}


def generate_tests():
    """
    Generate testing options for registry.load test.
    """
    tests_list = []
    for source in test_dict["source"]:
        for field in test_dict["field"]:
            nf_test_dir = (
                test_dir
                / "data"
                / f"{field.lower().replace(' ', '_')}"
                / source.lower()
            )
            for file in nf_test_dir.iterdir():
                if file.is_file() and file.name[0:3].isnumeric():
                    # Separate max_parameters from fields files
                    if (
                        source == "HFSS"
                        and file.suffix not in hfss_field_extensions[field]
                    ):
                        continue
                    tests_list.append((source, field, file))

    return tests_list


@pytest.mark.parametrize("source,field,file", generate_tests())
def test_loaders(source, field, file):
    """
    Test loaders.
    """
    result = registry.load(source, field, file)
    try:
        assert isinstance(result, xr.Dataset)
    except AssertionError as exc:
        raise AssertionError(
            f"Error processing test: {source, field, file} / {result}"
        ) from exc
