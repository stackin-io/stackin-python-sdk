#!/usr/bin/env python
"""CSOSN 400 — MEI/Simples equivalent of the exempt ICMS40."""

from _common import OTHER_STATE_ADDRESS, issue
from dotenv import load_dotenv

from stackin import Address
from stackin.br import CofinsNt, IcmsSn102, PisNt, Product, Tax

load_dotenv()


def main():
    product = Product(
        description="Rosa Holambra Vermelha",
        amount=112.44,
        ncm="06031100",
        cfop="6108",
        quantity=6,
        freight=11.05,
        tax=Tax(
            icms=IcmsSn102(orig="0", csosn="400"),
            pis=PisNt(cst="07"),
            cofins=CofinsNt(cst="07"),
        ),
    )
    issue(product, Address(**OTHER_STATE_ADDRESS))


if __name__ == "__main__":
    main()
