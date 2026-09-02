#!/usr/bin/env python
"""A real GTIN/EAN instead of the "SEM GTIN" default."""

from _common import SAME_STATE_ADDRESS, issue
from dotenv import load_dotenv

from stackin import Address
from stackin.br import Product

load_dotenv()


def main():
    product = Product(
        description="Produto com codigo de barras",
        amount=29.90,
        ncm="21069090",
        cfop="5102",
        barcode="7891000100103",
    )
    issue(product, Address(**SAME_STATE_ADDRESS))


if __name__ == "__main__":
    main()
