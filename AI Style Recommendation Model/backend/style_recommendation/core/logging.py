"""Configure logging once without replacing the host server's handlers."""
import logging


def configure_logging():
    logging.basicConfig(level=logging.INFO)
