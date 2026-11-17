"""Invoice __init__ module."""

__version__ = "0.16.0"
__description__ = (
    "Python SDK for issuing, consulting and cancelling electronic invoices."
)

from .core.address import Address
from .core.client import Invoice
from .core.exceptions import (
    APIError,
    CompanyNotInScopeError,
    CompanyRequiredError,
    ConnectionFailedError,
    InsufficientPermissionError,
    InvoiceError,
)
from .core.reference import KINDS, FiscalReference, Kind
from .core.taxpayer import Taxpayer
from .core.types import Direction, DocumentType, Environment, Manifestation, Purpose

__all__ = [
    "Invoice",
    "FiscalReference",
    "Kind",
    "KINDS",
    "Taxpayer",
    "DocumentType",
    "Environment",
    "Manifestation",
    "Purpose",
    "Direction",
    "Address",
    "InvoiceError",
    "APIError",
    "ConnectionFailedError",
    "CompanyRequiredError",
    "CompanyNotInScopeError",
    "InsufficientPermissionError",
]
