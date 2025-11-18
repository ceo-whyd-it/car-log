"""
e-Kasa API client for fetching receipt data.

Public endpoint provided by Financial Administration of Slovak Republic.
No authentication required.
"""

import requests
from typing import Dict
import logging

from .exceptions import APITimeoutError, ReceiptNotFoundError, EKasaError

logger = logging.getLogger(__name__)

EKASA_API_BASE_URL = "https://ekasa.financnasprava.sk/mdu/api/v1/opd/receipt"


def fetch_receipt_with_retry(
    receipt_id: str,
    timeout: int = 60,
    max_retries: int = 1
) -> Dict:
    """
    Fetch receipt from e-Kasa API with error handling.

    Args:
        receipt_id: e-Kasa receipt identifier
        timeout: Request timeout in seconds
        max_retries: Number of retry attempts for transient errors

    Returns:
        Receipt data dictionary

    Raises:
        APITimeoutError: Request exceeded timeout
        ReceiptNotFoundError: Receipt ID not found
        EKasaError: Other API errors
    """
    url = f"{EKASA_API_BASE_URL}/{receipt_id}"

    for attempt in range(max_retries + 1):
        try:
            logger.info(
                f"Fetching receipt {receipt_id} "
                f"(attempt {attempt + 1}/{max_retries + 1})"
            )

            response = requests.get(
                url,
                headers={'Accept': 'application/json'},
                timeout=timeout
            )

            # Handle HTTP errors
            if response.status_code == 404:
                raise ReceiptNotFoundError(
                    f"Receipt not found: {receipt_id}"
                )

            response.raise_for_status()

            data = response.json()
            logger.info(f"Receipt fetched successfully: {receipt_id}")
            return data

        except requests.Timeout:
            if attempt < max_retries:
                logger.warning(f"Timeout, retrying ({attempt + 1}/{max_retries})...")
                continue
            raise APITimeoutError(
                f"e-Kasa API timeout after {timeout}s"
            )

        except ReceiptNotFoundError:
            # Don't retry for 404
            raise

        except requests.RequestException as e:
            if attempt < max_retries:
                logger.warning(f"Request error, retrying: {e}")
                continue
            raise EKasaError(f"e-Kasa API error: {e}")

    raise EKasaError("All retry attempts failed")
