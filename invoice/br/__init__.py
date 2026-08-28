"""Brazil (BR) jurisdiction — public surface for concepts with no
meaning outside Brazil (NCM, CFOP, etc). Import from here, not from
`invoice` directly:

    from invoice.br import Product
"""

from invoice.core.br.product import PresumedCredit, Product

__all__ = ["Product", "PresumedCredit"]
