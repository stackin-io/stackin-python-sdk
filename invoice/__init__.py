"""Invoice __init__ module."""

__version__ = "0.5.0"
__description__ = "🧾 Human Python SDK for invoice-api — issue, consult, cancel NF-e/NFS-e with a handful of fields."

from .core.address import Address
from .core.br.product import Product
from .core.client import Invoice
from .core.exceptions import APIError, ConnectionFailedError, InvoiceError
from .core.types import DocumentType

__all__ = [
    "Invoice",
    "DocumentType",
    "Address",
    "Product",
    "InvoiceError",
    "APIError",
    "ConnectionFailedError",
]
