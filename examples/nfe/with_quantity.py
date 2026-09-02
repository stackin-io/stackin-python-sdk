#!/usr/bin/env python
"""Multiple units at a per-unit price."""

from _common import SAME_STATE_ADDRESS, issue
from dotenv import load_dotenv

from stackin import Address
from stackin.br import Product

load_dotenv()


def main():
    product = Product(
        description="Caixa de parafusos",
        amount=12.50,
        ncm="73181500",
        cfop="5102",
        unit="CX",
        quantity=20,
    )
    issue(product, Address(**SAME_STATE_ADDRESS))


if __name__ == "__main__":
    main()
