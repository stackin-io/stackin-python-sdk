#!/usr/bin/env python
"""Explicit service_code, overriding the company default (1.06)."""

from _common import issue
from dotenv import load_dotenv

from stackin.br import Product

load_dotenv()


def main():
    product = Product(
        description="Technical consulting - 10 hours",
        amount=1500.00,
        service_code="1.06",
    )
    issue(product)


if __name__ == "__main__":
    main()
