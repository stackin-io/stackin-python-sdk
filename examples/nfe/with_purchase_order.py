#!/usr/bin/env python
"""Linked to the buyer's purchase order and item number."""

from _common import SAME_STATE_ADDRESS, issue
from dotenv import load_dotenv

from stackin import Address
from stackin.br import Product

load_dotenv()

if __name__ == "__main__":
    product = Product(
        description="Produto vinculado a pedido de compra",
        amount=75.00,
        ncm="84433210",
        cfop="5102",
        purchase_order="PC-2026-00042",
        purchase_order_item="1",
    )
    issue(product, Address(**SAME_STATE_ADDRESS))
