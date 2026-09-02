#!/usr/bin/env python
"""ISSQN retained by the tomador — rejected (E0583) if the issuer is MEI."""

from _common import TOMADOR_ADDRESS, issue
from dotenv import load_dotenv

from stackin.br import Product

load_dotenv()

if __name__ == "__main__":
    product = Product(
        description="UI/UX design",
        amount=3200.00,
        service_code="1.03",
        tax_retained=True,
    )
    issue(product, TOMADOR_ADDRESS)
