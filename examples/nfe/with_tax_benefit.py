#!/usr/bin/env python
"""ICMS-ST item with a state tax benefit and presumed credit."""

from _common import SAME_STATE_ADDRESS, issue
from dotenv import load_dotenv

from stackin import Address
from stackin.br import PresumedCredit, Product

load_dotenv()


def main():
    product = Product(
        description="Produto com beneficio fiscal",
        amount=80.00,
        ncm="22021000",
        cfop="5102",
        cest="0300700",
        tax_benefit_code="PR820001",
        presumed_credits=[
            PresumedCredit(code="PR820001", percentage=3.0, amount=2.40),
        ],
    )
    issue(product, Address(**SAME_STATE_ADDRESS))


if __name__ == "__main__":
    main()
