"""Main entrypoint into xnft."""

import sys
import logging

from . import cli, gui

logger = logging.getLogger(__name__)


def main():
    """
    Main entrypoint function for xnft.

    If no arguments are provided, start xnft in GUI mode, otherwise parse user
    provided arguments.
    """
    if len(sys.argv) > 1:
        cli.main()
    else:
        gui.main()


if __name__ == "__main__":
    main()
