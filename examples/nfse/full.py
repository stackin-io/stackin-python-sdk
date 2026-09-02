#!/usr/bin/env python
"""Every optional field set at once."""

from _common import TOMADOR_ADDRESS, issue
from dotenv import load_dotenv

from stackin.br import Product

load_dotenv()

if __name__ == "__main__":
    product = Product(
        description="Software licensing",
        amount=1200.00,
        service_code="1.05",
        service_discount=100.00,
        tax_retained=True,
        observations="Licenca anual, renovacao automatica.",
    )
    issue(product, TOMADOR_ADDRESS)
