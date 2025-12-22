"""Module providing command line interfaces."""

import logging.config

# from importlib import resources

import click
import yaml

# TODO: REMOVE THESE LINES -- FOR TESTING ONLY
# import numpy as np
# import matplotlib.pyplot as plt

# Registers all loaders
import xnft.loaders  # noqa: F401  # pylint: disable=unused-import

from . import __version__
from .core.core import WELCOME_BANNER, nft
from .loaders.file_registry import registry

logger = logging.getLogger(__name__)


def configure_logging(
    config_path: str | None = None,  # default_config: str = "logging.dev.yaml"
):
    """
    Configure logging format.

    Parameters
    ----------
    config_path : _type_, optional
        _description_, by default None
    default_config : str, optional
        _description_, by default "logging.dev.yaml"
    """
    # if config_path is None:
    #     with resources.as_file(
    #         resources.files("xnft.resources") / default_config
    #     ) as p:
    if config_path is not None:
        with open(config_path, encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)
        logging.config.dictConfig(config_dict)


# @click.group(invoke_without_command=True)
@click.command()
@click.version_option(__version__, "--version", prog_name="xnft")
@click.option(
    "--log-config",
    type=click.Path(exists=True),
    help="Path to logging configuration YAML file.",
)
@click.option(
    "-s",
    "--source",
    type=click.Choice(
        ["hfss", "nsi", "lemma", "afrl"],
        case_sensitive=False,
    ),
    # prompt=True,
    required=True,
    help="Type of system that generated the near-field measurements data.",
)
@click.option(
    "-f",
    "--near-field-file",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        writable=False,
    ),
    # prompt="Near-field file path",
    required=True,
    help="Path to near-field file",
)
@click.option(
    "-r",
    "--far-field-file",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        writable=False,
    ),
    # prompt="Far-field file path",
    required=False,
    help="Path to far-field file",
)
# @click.pass_context
def main(
    source: str, near_field_file: str, far_field_file: str, log_config: str
) -> None:
    """
    Main CLI Entrypoint.
    """
    click.echo(WELCOME_BANNER)
    configure_logging(log_config)
    logger.debug(
        "source=%s:%s, near_field_file=%s:%s, far_field_file=%s:%s",
        source,
        type(source),
        near_field_file,
        type(near_field_file),
        far_field_file,
        type(far_field_file),
    )

    # Load near-field data
    near_field_data = registry.load(source, "near", near_field_file)

    # Load far-field data, if provided
    far_field_data = None
    if far_field_file:
        far_field_data = registry.load(source, "far", far_field_file)
        # e_mag_ff = np.linalg.norm(
        #     np.abs(far_field_data["E"]) ** 2, ord=2, axis=0
        # )
        # plt.imshow(e_mag_ff[:, :, 0])
        # plt.show()

    # Begin NFT computation
    nft(near_field_data, far_field_data)
