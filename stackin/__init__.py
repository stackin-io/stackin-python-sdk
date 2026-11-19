"""Invoice __init__ module."""

__version__ = "0.20.0"
__description__ = (
    "Python SDK for issuing, consulting and cancelling electronic invoices."
)

from .core.address import Address
from .core.client import Invoice
from .core.clients import Clients
from .core.exceptions import (
    APIError,
    ClientAlreadyExistsError,
    ClientInactiveError,
    ClientNotFoundError,
    CompanyNotInScopeError,
    CompanyRequiredError,
    ConnectionFailedError,
    InsufficientPermissionError,
    InvoiceError,
    PaymentRequiredError,
    RateLimitedError,
)
from .core.reference import KINDS, FiscalReference, Kind
from .core.taxpayer import Taxpayer
from .core.types import Direction, DocumentType, Environment, Manifestation, Purpose
from .core.usage import ReceivedSync, Usage

__all__ = [
    "Invoice",
    "Clients",
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
    "Usage",
    "ReceivedSync",
    "InvoiceError",
    "APIError",
    "ConnectionFailedError",
    "CompanyRequiredError",
    "CompanyNotInScopeError",
    "InsufficientPermissionError",
    "ClientAlreadyExistsError",
    "ClientInactiveError",
    "ClientNotFoundError",
    "PaymentRequiredError",
    "RateLimitedError",
]
