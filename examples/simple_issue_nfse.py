#!/usr/bin/env python
"""Minimal NFSE issuance — `api_key` (the issuing company's key,
POST /api/v1/companies) is the only thing stackin-api needs to
resolve the issuer's city/certificate. No Product here — NCM/CFOP
don't apply to a service.

Note: NFSE's signature algorithm is genuinely unconfirmed (see
plan/IMPLEMENTATION.md section 10), so this example is expected to
get a 501 from stackin-api today, not a successful issuance."""

import os

from dotenv import load_dotenv

from stackin import (
    APIError,
    ConnectionFailedError,
    DocumentType,
    Invoice,
)
from stackin.br import Product

load_dotenv()


class ServiceCatalog:
    """Builds Product examples for NFSE — only description/amount are
    used (stackin-api reads nothing else off the item for a service)."""

    @staticmethod
    def software_development():
        """A single development service."""
        return Product(description="Software development", amount=5000.00)

    @staticmethod
    def consulting():
        """A consulting service."""
        return Product(description="Technical consulting - 10 hours", amount=1500.00)

    @staticmethod
    def monthly_support():
        """A recurring support/maintenance service."""
        return Product(description="Monthly support and maintenance", amount=800.00)

    @staticmethod
    def design():
        """A design service."""
        return Product(description="UI/UX design", amount=3200.00)

    @classmethod
    def all(cls):
        """One instance of every service variant above — issue() only
        uses the first for NFSE, the rest are here for reference."""
        return [
            cls.software_development(),
            cls.consulting(),
            cls.monthly_support(),
            cls.design(),
        ]


def main():
    client = Invoice(api_key=os.environ.get("NFE_TEST_API_KEY"))

    try:
        result = client.issue(
            document_type=DocumentType.NFSE,
            client_name="John Doe",
            tax_id="00000000000",
            items=ServiceCatalog.all(),
        )
    except ConnectionFailedError:
        print("Could not reach stackin-api")
        return None
    except APIError as error:
        print(f"stackin-api rejected the request ({error.status_code}): "
              f"{error.detail}")
        return None

    print("Issued:", result)
    return result


if __name__ == "__main__":
    main()
