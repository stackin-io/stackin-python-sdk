"""Invoice __init__ module."""

__version__ = "0.9.0"
__description__ = (
    "Python SDK for issuing, consulting and cancelling electronic invoices."
)

from .core.address import Address
from .core.client import Invoice
from .core.exceptions import APIError, ConnectionFailedError, InvoiceError
from .core.reference import KINDS, FiscalReference, Kind
from .core.taxpayer import Taxpayer
from .core.types import DocumentType, Environment, Manifestation

__all__ = [
    "Invoice",
    "FiscalReference",
    "Kind",
    "KINDS",
    "Taxpayer",
    "DocumentType",
    "Environment",
    "Manifestation",
    "Address",
    "InvoiceError",
    "APIError",
    "ConnectionFailedError",
]
