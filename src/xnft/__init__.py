# Configure package logging
import logging
import logging.config
import yaml

logging.getLogger(__name__).addHandler(logging.NullHandler())

# Set package version number
__version__ = "0.1.0"


def configure_logging(
    config_path: str = "src/xnft/resources/logging.dev.yaml"
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
    if False and config_path is not None:
        with open(config_path, encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)
        logging.config.dictConfig(config_dict)


configure_logging()