"""
@snippet: read_odometer
@mcp: dashboard_ocr
@skill: ocr
@description: Read odometer value from dashboard photo using OCR
@triggers: read odometer, ocr dashboard, extract mileage, scan odometer
@params: image_path or image_base64
@returns: odometer reading in km
@version: 1.1

NOTE: This code is executed in the agent's code execution environment.
Adapters are available as globals: car_log_core, dashboard_ocr, etc.
DO NOT import adapters - use them directly.
"""

# Example usage:
# image_path = "/path/to/dashboard.jpg"  # or use image_base64

# Read odometer from image
result = await dashboard_ocr.read_odometer(image_path=image_path)

if result.get('success'):
    reading = result.get('odometer_km')
    confidence = result.get('confidence', 0)
    print(f"Odometer reading: {reading} km")
    print(f"Confidence: {confidence:.0%}")
else:
    print(f"Error reading odometer: {result.get('error')}")
    print("Please enter the odometer reading manually.")
