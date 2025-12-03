"""Test theory file loader."""

from pathlib import Path

import pytest

import xarray as xr

from xnft.loaders.file_registry import registry

test_dir = Path(__file__).parent.parent
test_dict = {"source": ["hfss", "theory"], "field": ["near", "far"]}


def generate_tests():
    """
    Generate testing options for registry.load test.
    """
    tests_list = []
    for source in test_dict["source"]:
        for field in test_dict["field"]:
            nf_test_dir = test_dir / "data" / f'{field}_field' / source
            for file in nf_test_dir.iterdir():
                if file.is_file() and file.name[0:3].isnumeric():
                    tests_list.append((source, field, file))

    return tests_list


@pytest.mark.parametrize('source,field,file', generate_tests())
def test_loaders(source, field, file):
    """
    Test loaders.
    """
    result = registry.load(source, field, file)
    try:
        assert isinstance(result, xr.Dataset)
    except AssertionError as exc:
        raise AssertionError(f'Error processing test: {source, field, file} / {result}') from exc

