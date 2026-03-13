# main.py
#
# Responsibility: Entry point. Orchestrate the full daily run.
#
# Run this file directly:   python main.py
# Or via cron:              0 6 * * * /path/to/venv/bin/python /path/to/main.py
#
# Change from original: after evaluator.is_below_threshold() returns True,
# llm_reasoner.get_fare_explanation() is called to generate a short analysis.
# The explanation is passed into notifier.send_alert() as llm_explanation.
# All other logic is unchanged.

import config
import api_client
import evaluator
import llm_reasoner
import notifier
import utils


def run_daily_check():
    """
    Execute the complete daily flight price check workflow.

    Steps:
    1. Load environment and configuration.
    2. Initialise logging.
    3. Create the Amadeus API client.
    4. For each configured route:
       a. Fetch flight offers.
       b. Extract the lowest fare.
       c. Compare to the threshold.
       d. If below threshold, get LLM explanation from DeepSeek.
       e. Send alert email with explanation included.
    5. Log a summary at the end of the run.
    """

    # ── Step 1: Load environment variables from .env ─────────────────────
    config.load_environment()

    # ── Step 2: Initialise logging ────────────────────────────────────────
    utils.setup_logging()
    logger = utils.get_logger(__name__)

    run_timestamp = utils.get_run_timestamp()
    logger.info(f"=== NGO Flight Monitor run started at {run_timestamp} ===")

    # ── Step 3: Load configuration ────────────────────────────────────────
    try:
        amadeus_id, amadeus_secret = config.get_amadeus_credentials()
        sg_key, from_email, to_emails = config.get_sendgrid_credentials()
        currency = config.get_currency()
        routes = config.parse_routes()
    except ValueError as config_error:
        logger.error(f"Configuration error: {config_error}")
        logger.error("Aborting run. Fix the .env file and try again.")
        return

    logger.info(
        f"Configuration loaded. "
        f"Checking {len(routes)} route(s) in {currency}."
    )

    # ── Step 4: Create the Amadeus API client ─────────────────────────────
    try:
        amadeus = api_client.create_amadeus_client(
            amadeus_id, amadeus_secret
        )
    except Exception as client_error:
        logger.error(f"Could not create Amadeus client: {client_error}")
        return

    # ── Step 5: Process each route ────────────────────────────────────────
    alerts_sent = 0

    for route in routes:
        origin      = route["origin"]
        destination = route["destination"]
        date        = route["date"]
        threshold   = route["threshold"]

        route_label = utils.format_route_label(origin, destination, date)
        logger.info(f"Processing route: {route_label}")

        # Fetch flight offers from Amadeus
        try:
            offers = api_client.fetch_flight_offers(
                amadeus_client=amadeus,
                origin=origin,
                destination=destination,
                departure_date=date,
                currency=currency,
            )
        except RuntimeError as api_error:
            logger.error(
                f"API error for {route_label}: {api_error}. "
                f"Skipping this route."
            )
            continue

        # Extract the lowest fare from the offers list
        lowest_fare = api_client.extract_lowest_fare(offers)

        if lowest_fare is None:
            logger.warning(
                f"No fare available for {route_label}. "
                f"Skipping this route."
            )
            continue

        logger.info(
            f"{route_label} — Lowest fare: {currency} {lowest_fare:.2f} "
            f"/ Threshold: {currency} {threshold:.2f}"
        )

        # Decide whether to send an alert
        should_alert = evaluator.is_below_threshold(lowest_fare, threshold)

        if should_alert:

            # ── NEW: Get LLM explanation from DeepSeek ────────────────────
            # The evaluator has already made the alert decision.
            # DeepSeek only generates a human-readable rationale.
            # If it fails, a fallback string is returned and the
            # email is still sent normally.
            explanation = llm_reasoner.get_fare_explanation(
                origin=origin,
                destination=destination,
                date=date,
                fare=lowest_fare,
                threshold=threshold,
                currency=currency,
            )
            # ─────────────────────────────────────────────────────────────

            success = notifier.send_alert(
                sendgrid_api_key=sg_key,
                from_email=from_email,
                to_emails=to_emails,
                origin=origin,
                destination=destination,
                date=date,
                fare=lowest_fare,
                threshold=threshold,
                currency=currency,
                llm_explanation=explanation,
            )
            if success:
                alerts_sent += 1

    # ── Step 6: Log run summary ───────────────────────────────────────────
    logger.info(
        f"=== Run complete. "
        f"{len(routes)} route(s) checked. "
        f"{alerts_sent} alert(s) sent. ==="
    )


if __name__ == "__main__":
    run_daily_check()
