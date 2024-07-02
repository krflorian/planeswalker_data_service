import logging
import requests
from typing import Any, Dict, Optional


def get_request(api_url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """
    Makes an HTTP GET request to the specified API URL and returns the response in JSON format.

    Args:
        api_url (str): URL to make the GET request to.
        timeout (int, optional): Timeout for the GET request in seconds. Defaults to 10.

    Returns:
        Optional[Dict[str, Any]]: The response JSON as a dictionary if successful, None otherwise.
    """
    logging.info(f"Initiating external request to {api_url}")

    try:
        response = requests.get(api_url, timeout=timeout)
        response.raise_for_status()  # Raise an HTTPError for bad responses

    except requests.exceptions.Timeout:
        logging.error(f"Request to {api_url} timed out after {timeout} seconds")
        return None

    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred while requesting {api_url}: {http_err}")
        return None

    except requests.exceptions.RequestException as err:
        logging.error(f"Error occurred while requesting {api_url}: {err}")
        return None

    try:
        json_data = response.json()
    except ValueError as json_err:
        logging.error(f"Error parsing JSON response from {api_url}: {json_err}")
        return None

    logging.info(f"Successfully received response from {api_url}")
    return json_data
