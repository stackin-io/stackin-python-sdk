#!/usr/bin/env python
"""Relevant-scale manufacturing indicator and its manufacturer CNPJ."""

from _common import SAME_STATE_ADDRESS, issue
from dotenv import load_dotenv

from stackin import Address
from stackin.br import Product

load_dotenv()

if __name__ == "__main__":
    product = Product(
        description="Produto de fabricacao em escala",
        amount=150.00,
        ncm="87141000",
        cfop="5102",
        cest="0100100",
        ind_escala="N",
        manufacturer_cnpj="12345678000195",
    )
    issue(product, Address(**SAME_STATE_ADDRESS))
