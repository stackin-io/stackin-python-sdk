#!/usr/bin/env python
"""A free-text note attached to the service."""

from _common import issue
from dotenv import load_dotenv

from stackin.br import Product

load_dotenv()

if __name__ == "__main__":
    product = Product(
        description="Systems analysis and development",
        amount=2400.00,
        service_code="1.01",
        observations="Referente ao contrato #2026-0042, etapa 2 de 3.",
    )
    issue(product)
