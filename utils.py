# utils.py
#
# Responsibility: Configure logging and provide shared utility functions.
# Every module that needs a logger calls get_logger() from this file.

import logging
import os
from datetime import datetime


LOG_DIR  = "logs"
LOG_FILE = os.path.join(LOG_DIR, "flight_monitor.log")


def setup_logging():
    """
    Configure the root Python logger once at startup.

    Log entries are written to both:
      - logs/flight_monitor.log  (persistent file)
      - the terminal console      (for manual runs)

    Each entry includes a timestamp, severity level, and message.
    This function should be called once at the start of main.py.
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    log_format = "%(asctime)s  %(levelname)-8s  %(name)s  |  %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def get_logger(name):
    """
    Return a named logger for the given module.

    Usage in any other module:
        from utils import get_logger
        logger = get_logger(__name__)
        logger.info("Something happened")

    Parameters:
        name (str): Typically pass __name__ so the log entry
                    shows which module generated it.

    Returns:
        logging.Logger
    """
    return logging.getLogger(name)


def format_route_label(origin, destination, date):
    """
    Return a short human-readable label for a route.

    Used in log messages and email subjects to identify which
    route triggered an alert.

    Parameters:
        origin      (str): IATA airport code, e.g. "JFK"
        destination (str): IATA airport code, e.g. "LHR"
        date        (str): Departure date, e.g. "2026-06-15"

    Returns:
        str: e.g. "JFK -> LHR (2026-06-15)"
    """
    return f"{origin} -> {destination} ({date})"


def get_run_timestamp():
    """
    Return the current date and time formatted as a string.

    Used to mark the start of each daily run in log output.

    Returns:
        str: e.g. "2026-03-02 06:00:00"
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
