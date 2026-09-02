#!/usr/bin/env python
"""Only description/amount — service_code falls back to the company's fiscal profile."""

from _common import issue
from dotenv import load_dotenv

from stackin.br import Product

load_dotenv()


def main():
    product = Product(description="Software development", amount=5000.00)
    issue(product)


if __name__ == "__main__":
    main()
