# notifier.py
#
# Responsibility: Build and send email alerts via the SendGrid API.
#
# This module receives the information it needs as function arguments.
# It does not read from config.py directly — main.py passes the
# credentials and route data in when it calls send_alert().
#
# Change from original: send_alert() accepts an optional
# llm_explanation argument. When provided, it is appended to the
# email body as an "AI Price Analysis" section. If not provided,
# the email body is identical to the original.

import sendgrid
from sendgrid.helpers.mail import Mail
from utils import get_logger

logger = get_logger(__name__)


def build_email_subject(origin, destination, date, fare, currency):
    """
    Build the subject line for the alert email.

    Parameters:
        origin      (str):   Departure airport code, e.g. "JFK".
        destination (str):   Arrival airport code, e.g. "LHR".
        date        (str):   Departure date, e.g. "2026-06-15".
        fare        (float): The fare that triggered the alert.
        currency    (str):   Currency code, e.g. "USD".

    Returns:
        str: A short subject line string.
    """
    subject = (
        f"Flight Alert: {origin} to {destination} on {date} — "
        f"{currency} {fare:.2f}"
    )
    return subject


def build_email_body(origin, destination, date, fare,
                     threshold, currency, llm_explanation=None):
    """
    Build the plain-text body for the alert email.

    Parameters:
        origin          (str):        Departure airport code.
        destination     (str):        Arrival airport code.
        date            (str):        Departure date.
        fare            (float):      The fare that triggered the alert.
        threshold       (float):      The threshold this fare fell below.
        currency        (str):        Currency code.
        llm_explanation (str | None): Optional explanation from DeepSeek.
                                      If provided, it is appended as an
                                      "AI Price Analysis" section.

    Returns:
        str: A multi-line plain-text email body.
    """
    body = (
        f"Flight Price Alert\n"
        f"{'=' * 40}\n\n"
        f"Route:          {origin} -> {destination}\n"
        f"Departure Date: {date}\n"
        f"Lowest Fare:    {currency} {fare:.2f}\n"
        f"Your Threshold: {currency} {threshold:.2f}\n"
        f"Saving:         {currency} {threshold - fare:.2f} below threshold\n\n"
        f"{'=' * 40}\n"
        f"This alert was generated automatically by the NGO Flight Monitor.\n"
        f"Please verify the fare on the Amadeus portal or your travel agent\n"
        f"before booking.\n"
    )

    # Append the LLM explanation if one was provided
    if llm_explanation:
        body += (
            f"\n{'=' * 40}\n"
            f"AI Price Analysis\n"
            f"{'=' * 40}\n"
            f"{llm_explanation}\n"
        )

    return body


def send_alert(
    sendgrid_api_key,
    from_email,
    to_emails,
    origin,
    destination,
    date,
    fare,
    threshold,
    currency,
    llm_explanation=None,
):
    """
    Send an email alert to all configured recipients via SendGrid.

    This function:
    1. Builds the subject and body using the helper functions above.
    2. Creates a SendGrid Mail object.
    3. Sends the email using the SendGrid API.
    4. Logs success or failure.

    Parameters:
        sendgrid_api_key (str):        Your SendGrid API key.
        from_email       (str):        Sender email address.
        to_emails        (list):       List of recipient email addresses.
        origin           (str):        Departure airport code.
        destination      (str):        Arrival airport code.
        date             (str):        Departure date.
        fare             (float):      The fare that triggered the alert.
        threshold        (float):      The configured threshold.
        currency         (str):        Currency code.
        llm_explanation  (str | None): Optional DeepSeek analysis text.
                                       Passed through to build_email_body().

    Returns:
        bool: True if the email was sent successfully, False otherwise.
    """
    subject = build_email_subject(
        origin, destination, date, fare, currency
    )
    body = build_email_body(
        origin, destination, date, fare, threshold, currency,
        llm_explanation=llm_explanation,
    )

    message = Mail(
        from_email=from_email,
        to_emails=to_emails,
        subject=subject,
        plain_text_content=body,
    )

    try:
        sg_client = sendgrid.SendGridAPIClient(api_key=sendgrid_api_key)
        response = sg_client.send(message)

        if response.status_code in (200, 201, 202):
            logger.info(
                f"Alert email sent successfully to "
                f"{len(to_emails)} recipient(s). "
                f"Status code: {response.status_code}."
            )
            return True
        else:
            logger.error(
                f"SendGrid returned unexpected status code: "
                f"{response.status_code}."
            )
            return False

    except Exception as error:
        logger.error(f"Failed to send alert email: {error}")
        return False
