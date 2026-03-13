# llm_reasoner.py
#
# Responsibility: Call the DeepSeek API to generate a short,
# human-readable explanation of why a fare is (or is not) a
# good deal. This explanation is appended to the alert email.
#
# IMPORTANT: This module does NOT decide whether an alert is sent.
# That decision is made exclusively by evaluator.is_below_threshold().
# This module is only called after that decision has already been made.
#
# If the DeepSeek API is unavailable for any reason, a safe fallback
# string is returned so the email workflow is never blocked.

import os
import requests
from utils import get_logger

logger = get_logger(__name__)

DEEPSEEK_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEEPSEEK_MODEL = "openrouter/free"


def get_deepseek_api_key():
    """
    Read the DeepSeek API key from the environment.

    The key is loaded via config.load_environment() / python-dotenv
    before this module is ever called, so os.environ is already
    populated from the .env file.

    Returns:
        str: The API key, or an empty string if not set.
    """
    return os.environ.get("DEEPSEEK_API_KEY", "")


def build_prompt(origin, destination, date, fare, threshold, currency):
    """
    Build the prompt sent to the DeepSeek model.

    Formats all relevant route and price details into a clear,
    structured message so the model has full context to produce
    a useful 2-3 sentence analysis.

    Parameters:
        origin      (str):   Departure airport IATA code, e.g. "JFK".
        destination (str):   Arrival airport IATA code, e.g. "LHR".
        date        (str):   Departure date, e.g. "2026-06-15".
        fare        (float): The fare that triggered the alert.
        threshold   (float): The configured threshold for this route.
        currency    (str):   Currency code, e.g. "USD".

    Returns:
        str: A formatted prompt string ready to send to the API.
    """
    prompt = (
        "You are a travel price analysis assistant.\n\n"
        "Evaluate the following airfare:\n\n"
        f"Route:           {origin} to {destination}\n"
        f"Departure date:  {date}\n"
        f"Current fare:    {currency} {fare:.2f}\n"
        f"Alert threshold: {currency} {threshold:.2f}\n\n"
        "In 2-3 sentences, explain whether this is a good deal "
        "and whether the traveller should consider booking soon."
    )
    return prompt


def get_fare_explanation(origin, destination, date, fare, threshold, currency):
    """
    Call the DeepSeek API and return a short fare analysis.

    Sends the prompt built by build_prompt() to the DeepSeek
    chat completions endpoint (OpenAI-compatible format) and
    returns the model's response text.

    On any failure — timeout, auth error, unexpected response
    format — a safe fallback string is returned so the rest of
    the workflow (i.e. sending the email) is never blocked.

    Parameters:
        origin      (str):   Departure airport IATA code.
        destination (str):   Arrival airport IATA code.
        date        (str):   Departure date.
        fare        (float): The fare that triggered the alert.
        threshold   (float): The configured threshold.
        currency    (str):   Currency code.

    Returns:
        str: A 2-3 sentence explanation from DeepSeek, or a
             fallback message if the API call fails.
    """
    api_key = get_deepseek_api_key()

    if not api_key:
        logger.warning(
            "DEEPSEEK_API_KEY is not set. "
            "Skipping LLM analysis. Add it to your .env file."
        )
        return "LLM analysis unavailable (API key not configured)."

    prompt = build_prompt(origin, destination, date, fare, threshold, currency)

    headers = {
        "Content-Type":  "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model":       DEEPSEEK_MODEL,
        "messages":    [{"role": "user", "content": prompt}],
        "max_tokens":  200,
        "temperature": 0.7,
    }

    try:
        logger.info(
            f"Calling DeepSeek for fare analysis: "
            f"{origin} -> {destination} at {currency} {fare:.2f}."
        )
        response = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
            timeout=20,
        )
        response.raise_for_status()

    
        response_data = response.json()
        choices = response_data.get("choices", [])
        if not choices:
            logger.warning(
                f"OpenRouter returned no choices. "
                f"Full response: {response_data}"
            )
            return "LLM analysis unavailable (empty response from model)."

        content = choices[0].get("message", {}).get("content")

        if not content:
            logger.warning(
                f"OpenRouter returned empty content. "
                f"Full response: {response_data}"
            )
            return "LLM analysis unavailable (empty response from model)."

        logger.info("LLM fare explanation received.")
        return content.strip()

        if not content:
            logger.warning(
                f"OpenRouter returned an empty response. "
                f"Full response: {response_data}"
            )
            return "LLM analysis unavailable (empty response from model)."

        logger.info("LLM fare explanation received.")
        return content.strip()

    except requests.exceptions.Timeout:
        logger.warning("DeepSeek API request timed out. Using fallback.")
        return "LLM analysis unavailable (request timed out)."

    except requests.exceptions.RequestException as error:
        logger.error(f"DeepSeek API request failed: {error}")
        return "LLM analysis unavailable (API error)."

    except (KeyError, IndexError, ValueError) as error:
        logger.error(f"Could not parse DeepSeek response: {error}")
        return "LLM analysis unavailable (unexpected response format)."
