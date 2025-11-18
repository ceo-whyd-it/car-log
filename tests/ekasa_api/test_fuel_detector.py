"""
Unit tests for fuel detection from Slovak receipt items.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../mcp-servers'))

import pytest
from ekasa_api.fuel_detector import detect_fuel_type, extract_fuel_data


class TestFuelDetection:
    """Test Slovak fuel name pattern matching"""

    def test_detect_diesel_variants(self):
        """Test detection of various Diesel names"""
        assert detect_fuel_type("Diesel") == "Diesel"
        assert detect_fuel_type("DIESEL") == "Diesel"
        assert detect_fuel_type("Nafta") == "Diesel"
        assert detect_fuel_type("Motorová nafta") == "Diesel"

    def test_detect_gasoline_95_variants(self):
        """Test detection of Gasoline 95 variants"""
        assert detect_fuel_type("Natural 95") == "Gasoline_95"
        assert detect_fuel_type("NATURAL95") == "Gasoline_95"
        assert detect_fuel_type("BA 95") == "Gasoline_95"
        assert detect_fuel_type("Benzín 95") == "Gasoline_95"

    def test_detect_gasoline_98_variants(self):
        """Test detection of Gasoline 98 variants"""
        assert detect_fuel_type("Natural 98") == "Gasoline_98"
        assert detect_fuel_type("BA 98") == "Gasoline_98"
        assert detect_fuel_type("Benzín 98") == "Gasoline_98"

    def test_detect_lpg_variants(self):
        """Test detection of LPG variants"""
        assert detect_fuel_type("LPG") == "LPG"
        assert detect_fuel_type("lpg") == "LPG"
        assert detect_fuel_type("Autoplyn") == "LPG"

    def test_detect_cng_variants(self):
        """Test detection of CNG variants"""
        assert detect_fuel_type("CNG") == "CNG"
        assert detect_fuel_type("Zemný plyn") == "CNG"

    def test_non_fuel_items(self):
        """Test that non-fuel items return None"""
        assert detect_fuel_type("Káva") is None
        assert detect_fuel_type("Minerálka") is None
        assert detect_fuel_type("Hot dog") is None


class TestFuelDataExtraction:
    """Test extraction of fuel data from e-Kasa receipt"""

    def test_extract_fuel_data_diesel(self):
        """Test extraction of Diesel fuel data"""
        receipt_data = {
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

        fuel_data = extract_fuel_data(receipt_data)

        assert fuel_data['fuel_type'] == "Diesel"
        assert fuel_data['quantity_liters'] == 45.5
        assert fuel_data['price_per_liter'] == 1.44
        assert fuel_data['total_price'] == 65.52
        assert fuel_data['vat_amount'] == 10.92
        assert fuel_data['vat_rate'] == 20

    def test_extract_fuel_data_multiple_items(self):
        """Test extraction when receipt has multiple items"""
        receipt_data = {
            "items": [
                {"name": "Káva", "quantity": 1},
                {"name": "Natural 95", "quantity": 30.0, "unitPrice": 1.65, "totalPrice": 49.50, "vatAmount": 8.25, "vatRate": 20},
                {"name": "Minerálka", "quantity": 1}
            ]
        }

        fuel_data = extract_fuel_data(receipt_data)

        assert fuel_data['fuel_type'] == "Gasoline_95"
        assert fuel_data['quantity_liters'] == 30.0

    def test_extract_fuel_data_no_fuel(self):
        """Test error when no fuel items present"""
        receipt_data = {
            "items": [
                {"name": "Káva", "quantity": 1},
                {"name": "Minerálka", "quantity": 1}
            ]
        }

        with pytest.raises(ValueError, match="No fuel items found"):
            extract_fuel_data(receipt_data)

    def test_extract_fuel_data_empty_items(self):
        """Test error when items array is empty"""
        receipt_data = {"items": []}

        with pytest.raises(ValueError, match="No fuel items found"):
            extract_fuel_data(receipt_data)
