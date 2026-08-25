"""Exceptions module."""


class InvoiceError(Exception):
    """Base exception for the invoice SDK."""


class APIError(InvoiceError):
    """
    Raised when the invoice API responds with a non-2xx status.

    Args:
        status_code (int): HTTP status returned by the API.
        detail (str): The API's `detail` field, or raw body if absent.
    """

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"[{status_code}] {detail}")


class ConnectionFailedError(InvoiceError):
    """Raised when the invoice API can't be reached at all
    (network/DNS/timeout)."""
