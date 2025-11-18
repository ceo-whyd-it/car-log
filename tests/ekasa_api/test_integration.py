"""
Integration tests for ekasa-api MCP server.

These tests demonstrate the complete workflow but use mock data.
For real e-Kasa API testing, run with actual receipt files.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../mcp-servers'))

import pytest
from pathlib import Path
from unittest.mock import patch, Mock


@pytest.mark.asyncio
class TestEKasaWorkflow:
    """Test complete e-Kasa workflow"""

    @pytest.mark.skip(reason="Requires pyzbar and PIL for QR scanning (optional integration test)")
    @patch('pyzbar.pyzbar.decode')
    @patch('requests.get')
    async def test_full_workflow_mock(self, mock_get, mock_decode):
        """Test complete workflow: Image -> QR -> API -> Fuel data"""
        from ekasa_api.tools.scan_qr_code import scan_qr_code
        from ekasa_api.tools.fetch_receipt_data import fetch_receipt_data

        # Mock QR detection
        mock_qr = Mock()
        mock_qr.data.decode.return_value = "O-E182401234567890123456789"
        mock_decode.return_value = [mock_qr]

        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "receiptId": "O-E182401234567890123456789",
            "createDate": "2025-11-18T14:30:00Z",
            "organization": {
                "organizationName": "Shell Slovakia s.r.o.",
                "ico": "12345678"
            },
            "totalPrice": 65.50,
            "totalVat": 10.92,
            "items": [
                {
                    "name": "Diesel",
                    "quantity": 45.5,
                    "unitPrice": 1.44,
                    "totalPrice": 65.52,
                    "vatAmount": 10.92,
                    "vatRate": 20
                }
            ]
        }
        mock_get.return_value = mock_response

        # Step 1: Scan QR (would need real image file, using mock)
        # For real test: qr_result = await scan_qr_code("/path/to/receipt.pdf")

        # Step 2: Fetch receipt data
        receipt_id = "O-E182401234567890123456789"
        api_result = await fetch_receipt_data(receipt_id)

        # Verify results
        assert api_result['success'] is True
        assert api_result['receipt_data']['vendor_name'] == "Shell Slovakia s.r.o."
        assert api_result['receipt_data']['total_amount_eur'] == 65.50

        # Verify fuel data extraction
        assert len(api_result['fuel_items']) == 1
        fuel = api_result['fuel_items'][0]
        assert fuel['fuel_type'] == "Diesel"
        assert fuel['quantity_liters'] == 45.5
        assert fuel['price_per_liter'] == 1.44
