"""Brazil-specific document fields."""

from invoice.core.br.product import PresumedCredit, Product
from invoice.core.br.tax import (
    CofinsAliq,
    CofinsNt,
    CofinsOutr,
    Icms00,
    Icms40,
    Icms60,
    IcmsSn101,
    IcmsSn102,
    IcmsUfDest,
    Ipi,
    IpiNt,
    IpiTrib,
    PisAliq,
    PisNt,
    PisOutr,
    Tax,
)

__all__ = [
    "Product",
    "PresumedCredit",
    "Tax",
    "Icms00",
    "Icms40",
    "Icms60",
    "IcmsSn101",
    "IcmsSn102",
    "IcmsUfDest",
    "Ipi",
    "IpiTrib",
    "IpiNt",
    "PisAliq",
    "PisNt",
    "PisOutr",
    "CofinsAliq",
    "CofinsNt",
    "CofinsOutr",
]
