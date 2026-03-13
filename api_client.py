# api_client.py
#
# Responsibility: Authenticate with Amadeus and fetch the lowest
# available fare for a given flight route.
#
# The Amadeus SDK handles OAuth2 token refresh automatically.
# All API errors are caught here and re-raised with clear messages.

from amadeus import Client, ResponseError
from utils import get_logger

logger = get_logger(__name__)


def create_amadeus_client(client_id, client_secret):
    """
    Create and return an authenticated Amadeus API client.

    The SDK authenticates using the client credentials OAuth2 flow.
    It automatically refreshes the access token before it expires.

    Parameters:
        client_id     (str): Your Amadeus API client ID.
        client_secret (str): Your Amadeus API client secret.

    Returns:
        amadeus.Client: An authenticated client instance.

    Raises:
        Exception: If the client cannot be initialised.
    """
    logger.info("Creating Amadeus API client.")

    amadeus_client = Client(
        client_id=client_id,
        client_secret=client_secret,
    )

    return amadeus_client


def fetch_flight_offers(amadeus_client, origin, destination,
                        departure_date, currency, adults=1):
    """
    Call the Amadeus Flight Offers Search API for a single route.

    Requests up to 5 offers sorted by price so the cheapest
    option is always first in the response.

    Parameters:
        amadeus_client  (amadeus.Client): Authenticated client.
        origin          (str): Departure airport IATA code, e.g. "JFK".
        destination     (str): Arrival airport IATA code, e.g. "LHR".
        departure_date  (str): Departure date in YYYY-MM-DD format.
        currency        (str): Currency code for prices, e.g. "USD".
        adults          (int): Number of adult passengers. Default is 1.

    Returns:
        list: A list of flight offer dictionaries from the API response.
              Returns an empty list if the API returns no results.

    Raises:
        RuntimeError: If the API returns an error response.
    """
    logger.info(
        f"Fetching flight offers: {origin} -> {destination} "
        f"on {departure_date} in {currency}."
    )

    try:
        response = amadeus_client.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            adults=adults,
            currencyCode=currency,
            max=5,
        )
    except ResponseError as error:
        raise RuntimeError(
            f"Amadeus API error for {origin} -> {destination}: "
            f"{error.response.result}"
        )

    offers = response.data

    if not offers:
        logger.warning(
            f"No flight offers returned for "
            f"{origin} -> {destination} on {departure_date}."
        )
        return []

    logger.info(
        f"Received {len(offers)} offer(s) for "
        f"{origin} -> {destination}."
    )

    return offers


def extract_lowest_fare(flight_offers):
    """
    Extract the lowest total fare from a list of flight offers.

    The Amadeus API returns offers sorted cheapest-first when
    max=5 is used. This function reads the price from the first
    offer in the list.

    Parameters:
        flight_offers (list): The list returned by fetch_flight_offers().

    Returns:
        float: The lowest total fare as a floating-point number.
               Returns None if the list is empty or price is missing.
    """
    if not flight_offers:
        logger.warning("No flight offers to extract fare from.")
        return None

    first_offer = flight_offers[0]

    try:
        price_str = first_offer["price"]["grandTotal"]
        lowest_fare = float(price_str)
    except (KeyError, TypeError, ValueError) as error:
        logger.error(
            f"Could not extract fare from offer data: {error}"
        )
        return None

    logger.info(f"Lowest fare extracted: {lowest_fare}")

    return lowest_fare
