"""
Custom exceptions for e-Kasa API operations.
"""


class EKasaError(Exception):
    """Base exception for e-Kasa API errors"""
    pass


class QRDetectionError(EKasaError):
    """QR code detection failed"""
    pass


class APITimeoutError(EKasaError):
    """API request timed out"""
    pass


class ReceiptNotFoundError(EKasaError):
    """Receipt ID not found in e-Kasa system"""
    pass


class NoFuelItemsError(EKasaError):
    """No fuel items found in receipt"""
    pass
