# Configure package logging
import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())

# Set package version number
__version__ = "0.1.0"
