#!/usr/bin/env python
"""A used movable asset being resold."""

from _common import SAME_STATE_ADDRESS, issue
from dotenv import load_dotenv

from stackin import Address
from stackin.br import Product

load_dotenv()

if __name__ == "__main__":
    product = Product(
        description="Bem movel usado",
        amount=500.00,
        ncm="87032310",
        cfop="5102",
        used_movable_asset=True,
    )
    issue(product, Address(**SAME_STATE_ADDRESS))
