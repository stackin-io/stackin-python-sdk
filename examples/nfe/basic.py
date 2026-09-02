#!/usr/bin/env python
"""Only what NFE requires: description, amount, ncm, cfop."""

from _common import SAME_STATE_ADDRESS, issue
from dotenv import load_dotenv

from stackin import Address
from stackin.br import Product

load_dotenv()


def main():
    product = Product(
        description="Produto basico",
        amount=50.00,
        ncm="84713012",
        cfop="5102",
    )
    issue(product, Address(**SAME_STATE_ADDRESS))


if __name__ == "__main__":
    main()
