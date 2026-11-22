"""Invoice __init__ module."""

__version__ = "0.24.1"
__description__ = (
    "Python SDK for issuing, consulting and cancelling electronic invoices."
)

from .core.address import Address
from .core.client import Invoice
from .core.clients import Clients
from .core.company import Company
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
    ItemAlreadyExistsError,
    ItemInactiveError,
    ItemKindMismatchError,
    ItemNotFoundError,
    ItemTaxRegimeMismatchError,
    ItemTaxRequiredError,
    PaymentRequiredError,
    RateLimitedError,
)
from .core.items import CatalogItem, Items, ItemSaved
from .core.reference import KINDS, FiscalReference, Kind
from .core.taxpayer import Taxpayer
from .core.types import Direction, DocumentType, Environment, Manifestation, Purpose
from .core.usage import ReceivedSync, Usage
from .core.webhooks import EVENTS, Webhooks

__all__ = [
    "Invoice",
    "Clients",
    "Items",
    "CatalogItem",
    "ItemSaved",
    "Webhooks",
    "Company",
    "EVENTS",
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
    "ItemAlreadyExistsError",
    "ItemNotFoundError",
    "ItemInactiveError",
    "ItemKindMismatchError",
    "ItemTaxRequiredError",
    "ItemTaxRegimeMismatchError",
    "PaymentRequiredError",
    "RateLimitedError",
]
