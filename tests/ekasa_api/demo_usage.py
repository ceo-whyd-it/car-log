"""
Demonstration of ekasa-api MCP server functionality.

This script shows example usage of the QR scanning and receipt fetching tools.
"""

import asyncio
from mcp_servers.ekasa_api.fuel_detector import detect_fuel_type, extract_fuel_data


def demo_fuel_detection():
    """Demonstrate Slovak fuel name pattern matching"""
    print("=" * 60)
    print("FUEL DETECTION DEMO")
    print("=" * 60)

    test_names = [
        "Diesel",
        "NAFTA",
        "Natural 95",
        "BA 98",
        "Benzín 95",
        "LPG",
        "Autoplyn",
        "CNG",
        "Káva",  # Non-fuel
        "Minerálka"  # Non-fuel
    ]

    for name in test_names:
        fuel_type = detect_fuel_type(name)
        status = fuel_type if fuel_type else "Not fuel"
        print(f"  {name:20} -> {status}")

    print()


def demo_receipt_parsing():
    """Demonstrate receipt data extraction"""
    print("=" * 60)
    print("RECEIPT PARSING DEMO")
    print("=" * 60)

    # Example e-Kasa receipt response
    receipt_data = {
        "receiptId": "O-E182401234567890123456789",
        "createDate": "2025-11-18T14:30:00Z",
        "organization": {
            "organizationName": "Shell Slovakia s.r.o.",
            "ico": "12345678",
            "dic": "SK1234567890",
            "address": {
                "street": "Hlavná",
                "buildingNumber": "45",
                "city": "Bratislava",
                "postalCode": "811 01"
            }
        },
        "items": [
            {
                "name": "Diesel",
                "quantity": 45.5,
                "unit": "l",
                "unitPrice": 1.44,
                "totalPrice": 65.52,
                "vatRate": 20,
                "priceWithoutVat": 54.60,
                "vatAmount": 10.92
            }
        ],
        "totalPrice": 65.50,
        "totalPriceWithoutVat": 54.58,
        "totalVat": 10.92
    }

    print(f"Receipt ID: {receipt_data['receiptId']}")
    print(f"Vendor: {receipt_data['organization']['organizationName']}")
    print(f"Total: €{receipt_data['totalPrice']:.2f}")
    print()

    # Extract fuel data
    try:
        fuel_data = extract_fuel_data(receipt_data)
        print("Fuel Item Detected:")
        print(f"  Type: {fuel_data['fuel_type']}")
        print(f"  Quantity: {fuel_data['quantity_liters']} liters")
        print(f"  Price per liter: €{fuel_data['price_per_liter']:.2f}")
        print(f"  Total price: €{fuel_data['total_price']:.2f}")
        print(f"  VAT: €{fuel_data['vat_amount']:.2f} ({fuel_data['vat_rate']}%)")
    except ValueError as e:
        print(f"Error: {e}")

    print()


async def demo_mcp_tools():
    """Demonstrate MCP tool responses (mock)"""
    print("=" * 60)
    print("MCP TOOL RESPONSE DEMO")
    print("=" * 60)

    # Example scan_qr_code response
    qr_result = {
        "success": True,
        "receipt_id": "O-E182401234567890123456789",
        "confidence": 1.0,
        "detection_scale": 2.0,
        "format": "pdf",
        "error": None
    }

    print("scan_qr_code response:")
    for key, value in qr_result.items():
        print(f"  {key}: {value}")
    print()

    # Example fetch_receipt_data response
    fetch_result = {
        "success": True,
        "receipt_data": {
            "receipt_id": "O-E182401234567890123456789",
            "vendor_name": "Shell Slovakia s.r.o.",
            "vendor_tax_id": "12345678",
            "timestamp": "2025-11-18T14:30:00Z",
            "total_amount_eur": 65.50,
            "vat_amount_eur": 10.92
        },
        "fuel_items": [
            {
                "fuel_type": "Diesel",
                "quantity_liters": 45.5,
                "price_per_liter": 1.44,
                "total_price": 65.52,
                "vat_amount": 10.92,
                "vat_rate": 20.0
            }
        ],
        "error": None
    }

    print("fetch_receipt_data response:")
    print(f"  Success: {fetch_result['success']}")
    print(f"  Vendor: {fetch_result['receipt_data']['vendor_name']}")
    print(f"  Total: €{fetch_result['receipt_data']['total_amount_eur']:.2f}")
    print(f"  Fuel items: {len(fetch_result['fuel_items'])}")

    if fetch_result['fuel_items']:
        fuel = fetch_result['fuel_items'][0]
        print(f"    - {fuel['fuel_type']}: {fuel['quantity_liters']}L @ €{fuel['price_per_liter']:.2f}/L")

    print()


def main():
    """Run all demonstrations"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "ekasa-api MCP Server Demo" + " " * 23 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    demo_fuel_detection()
    demo_receipt_parsing()
    asyncio.run(demo_mcp_tools())

    print("=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
