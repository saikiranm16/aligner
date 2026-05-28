import logging
import sys


def configure_logging() -> None:
    """Configure structured-enough console logging for service diagnostics."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

