#!/usr/bin/env python
"""Freight, insurance, discount, and other expenses on the item."""

from _common import SAME_STATE_ADDRESS, issue
from dotenv import load_dotenv

from stackin import Address
from stackin.br import Product

load_dotenv()

if __name__ == "__main__":
    product = Product(
        description="Produto com encargos adicionais",
        amount=200.00,
        ncm="94036000",
        cfop="5102",
        freight=15.00,
        insurance=5.00,
        discount=10.00,
        other_expenses=3.50,
    )
    issue(product, Address(**SAME_STATE_ADDRESS))
