#!/usr/bin/env python
"""An unconditional discount applied to the service value."""

from _common import issue
from dotenv import load_dotenv

from stackin.br import Product

load_dotenv()


def main():
    product = Product(
        description="Monthly support and maintenance",
        amount=800.00,
        service_code="1.07",
        service_discount=50.00,
    )
    issue(product)


if __name__ == "__main__":
    main()
