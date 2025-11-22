"""
Unit tests for e-Kasa API client.

Note: These tests require mocking or actual API access.
Integration tests should be run separately.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../mcp-servers'))

import pytest
from unittest.mock import patch, Mock
from ekasa_api.api_client import fetch_receipt_with_retry
from ekasa_api.exceptions import (
    APITimeoutError,
    ReceiptNotFoundError
)


class TestAPIClient:
    """Test e-Kasa API client functionality"""

    @patch('ekasa_api.api_client.requests.get')
    def test_fetch_receipt_success(self, mock_get):
        """Test successful receipt fetch"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "receiptId": "O-E182401234567890123456789",
            "organization": {"organizationName": "Shell Slovakia"},
            "totalPrice": 65.50
        }
        mock_get.return_value = mock_response

        result = fetch_receipt_with_retry("O-E182401234567890123456789")

        assert result['receiptId'] == "O-E182401234567890123456789"
        assert result['totalPrice'] == 65.50

    @patch('ekasa_api.api_client.requests.get')
    def test_fetch_receipt_not_found(self, mock_get):
        """Test 404 receipt not found"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with pytest.raises(ReceiptNotFoundError, match="Receipt not found"):
            fetch_receipt_with_retry("invalid-id")

    @patch('ekasa_api.api_client.requests.get')
    def test_fetch_receipt_timeout(self, mock_get):
        """Test API timeout handling"""
        import requests
        mock_get.side_effect = requests.Timeout()

        with pytest.raises(APITimeoutError, match="timeout"):
            fetch_receipt_with_retry("test-id", timeout=60, max_retries=0)

    @patch('ekasa_api.api_client.requests.get')
    def test_fetch_receipt_retry_success(self, mock_get):
        """Test retry mechanism works"""
        import requests

        # First call times out, second succeeds
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"receiptId": "test"}

        mock_get.side_effect = [
            requests.Timeout(),
            mock_response
        ]

        result = fetch_receipt_with_retry("test-id", max_retries=1)

        assert result['receiptId'] == "test"
        assert mock_get.call_count == 2
