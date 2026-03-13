# evaluator.py
#
# Responsibility: Compare a fetched fare to a predefined threshold
# and determine whether an alert should be sent.
#
# This module contains no API calls, no email logic, and no
# configuration loading. It does one comparison and returns a result.

from utils import get_logger

logger = get_logger(__name__)


def is_below_threshold(fare, threshold):
    """
    Determine whether a given fare is below the alert threshold.

    This is the core decision function. If it returns True, the
    calling code in main.py will trigger an email alert.

    Parameters:
        fare      (float): The lowest fare returned by the API.
                           Can be None if no fare was retrieved.
        threshold (float): The maximum acceptable fare configured
                           for this route.

    Returns:
        bool: True if fare is strictly less than threshold.
              False in all other cases, including if fare is None.
    """
    if fare is None:
        logger.warning(
            "Fare is None. Cannot compare to threshold. "
            "Skipping alert for this route."
        )
        return False

    if fare < threshold:
        logger.info(
            f"Fare {fare} is below threshold {threshold}. "
            f"Alert will be sent."
        )
        return True

    logger.info(
        f"Fare {fare} is at or above threshold {threshold}. "
        f"No alert needed."
    )
    return False
