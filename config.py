# config.py
#
# Responsibility: Load all configuration from environment variables.
# Every other module imports from this file rather than reading
# environment variables directly. This keeps configuration changes
# in one place.

import os
from dotenv import load_dotenv


def load_environment():
    """
    Load the .env file into the process environment.

    This function must be called once, at the start of main.py,
    before any other configuration functions are used.
    """
    load_dotenv()


def get_amadeus_credentials():
    """
    Return the Amadeus API client ID and secret as a tuple.

    Raises ValueError if either credential is missing from the environment.
    """
    client_id = os.environ.get("AMADEUS_CLIENT_ID")
    client_secret = os.environ.get("AMADEUS_CLIENT_SECRET")

    if not client_id:
        raise ValueError(
            "AMADEUS_CLIENT_ID is not set. "
            "Add it to your .env file."
        )
    if not client_secret:
        raise ValueError(
            "AMADEUS_CLIENT_SECRET is not set. "
            "Add it to your .env file."
        )

    return client_id, client_secret


def get_sendgrid_credentials():
    """
    Return the SendGrid API key, sender address, and list
    of recipient addresses.

    Raises ValueError if any required value is missing.
    """
    api_key = os.environ.get("SENDGRID_API_KEY")
    from_email = os.environ.get("ALERT_FROM_EMAIL")
    to_emails_raw = os.environ.get("ALERT_TO_EMAILS")

    if not api_key:
        raise ValueError("SENDGRID_API_KEY is not set.")
    if not from_email:
        raise ValueError("ALERT_FROM_EMAIL is not set.")
    if not to_emails_raw:
        raise ValueError("ALERT_TO_EMAILS is not set.")

    # Split on comma to support multiple recipients
    to_emails = [addr.strip() for addr in to_emails_raw.split(",")]

    return api_key, from_email, to_emails


def get_currency():
    """
    Return the currency code used for threshold comparisons.
    Defaults to USD if not explicitly configured.
    """
    return os.environ.get("CURRENCY", "USD")


def parse_routes():
    """
    Parse the ROUTES environment variable into a list of
    route dictionaries.

    The raw format for each route entry is:
        ORIGIN-DESTINATION-DATE-THRESHOLD

    Example raw value:
        JFK-LHR-2026-06-15-500|CDG-NBO-2026-07-01-700

    Multiple routes are separated by a pipe character (|).

    Returns a list of dicts, each with keys:
        origin      (str)   e.g. "JFK"
        destination (str)   e.g. "LHR"
        date        (str)   e.g. "2026-06-15"
        threshold   (float) e.g. 500.0

    Raises ValueError if the ROUTES variable is missing or
    if any individual route entry is malformed.
    """
    raw = os.environ.get("ROUTES")

    if not raw:
        raise ValueError(
            "ROUTES is not set. "
            "Add it to your .env file."
        )

    route_entries = raw.split("|")
    parsed_routes = []

    for entry in route_entries:
        entry = entry.strip()
        parts = entry.split("-")

        # Expected parts: ORIGIN DEST YEAR MONTH DAY THRESHOLD
        # e.g. JFK-LHR-2026-06-15-500 splits into 6 parts
        if len(parts) != 6:
            raise ValueError(
                f"Route entry '{entry}' is malformed. "
                f"Expected format: ORIGIN-DEST-YYYY-MM-DD-THRESHOLD "
                f"e.g. JFK-LHR-2026-06-15-500"
            )

        origin      = parts[0].upper()
        destination = parts[1].upper()
        date        = f"{parts[2]}-{parts[3]}-{parts[4]}"
        threshold   = float(parts[5])

        parsed_routes.append({
            "origin":      origin,
            "destination": destination,
            "date":        date,
            "threshold":   threshold,
        })

    return parsed_routes
