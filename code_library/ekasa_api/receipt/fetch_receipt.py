"""
@snippet: fetch_receipt
@mcp: ekasa_api
@skill: receipt
@description: Fetch receipt data from Slovak e-Kasa system using QR code
@triggers: fetch receipt, get receipt, ekasa receipt, scan receipt, qr code
@params: receipt_id or qr_data
@returns: receipt data with fuel info
@version: 1.1

NOTE: This code is executed in the agent's code execution environment.
Adapters are available as globals: car_log_core, ekasa_api, etc.
DO NOT import adapters - use them directly.
"""

# Example usage:
# receipt_id = "O-12345678901234567890"  # or qr_data from scan

print("Fetching receipt from e-Kasa (this may take up to 30 seconds)...")

result = await ekasa_api.fetch_receipt(receipt_id=receipt_id)

if result.get('success'):
    receipt = result.get('receipt', {})
    print(f"Receipt fetched successfully!")
    print(f"  Vendor: {receipt.get('vendor_name', 'N/A')}")
    print(f"  Date: {receipt.get('datetime', 'N/A')}")
    print(f"  Total: {receipt.get('total_amount', 0):.2f} EUR")

    # Check for fuel items
    fuel_items = receipt.get('fuel_items', [])
    if fuel_items:
        print("Fuel Items:")
        for item in fuel_items:
            fuel_type = item.get('fuel_type', 'Unknown')
            liters = item.get('liters', 0)
            price = item.get('price_per_liter', 0)
            print(f"  {fuel_type}: {liters:.2f}L @ {price:.3f} EUR/L")
    else:
        print("  No fuel items detected in receipt")
else:
    print(f"Error fetching receipt: {result.get('error')}")
    print("The receipt may not exist or e-Kasa API is unavailable.")
