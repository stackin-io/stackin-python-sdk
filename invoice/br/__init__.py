"""Brazil (BR) jurisdiction — public surface for concepts with no
meaning outside Brazil (NCM, CFOP, etc). Import from here, not from
`invoice` directly:

    from invoice.br import Product
"""

from invoice.core.br.product import PresumedCredit, Product
from invoice.core.br.tax import (
    CofinsAliq,
    CofinsNt,
    Icms00,
    Icms40,
    IcmsSn101,
    IcmsSn102,
    IcmsUfDest,
    PisAliq,
    PisNt,
    Tax,
)

__all__ = [
    "Product",
    "PresumedCredit",
    "Tax",
    "Icms00",
    "Icms40",
    "IcmsSn101",
    "IcmsSn102",
    "IcmsUfDest",
    "PisAliq",
    "PisNt",
    "CofinsAliq",
    "CofinsNt",
]
