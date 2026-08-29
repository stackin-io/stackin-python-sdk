"""Invoice __init__ module."""

__version__ = "0.8.0"
__description__ = "🧾 Human Python SDK for stackin-api — issue, consult, cancel NF-e/NFS-e with a handful of fields."

from .core.address import Address
from .core.client import Invoice
from .core.exceptions import APIError, ConnectionFailedError, InvoiceError
from .core.types import DocumentType

__all__ = [
    "Invoice",
    "DocumentType",
    "Address",
    "InvoiceError",
    "APIError",
    "ConnectionFailedError",
]
