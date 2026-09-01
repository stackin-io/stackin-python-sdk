#!/usr/bin/env python
"""NFSE issuance — every field here is optional except
description/amount:

- service_code: LC 116/2003 item.subitem (e.g. "1.07"). Falls back
  to the company's fiscal profile when omitted.
- discount: unconditional discount (vDescIncond).
- tax_retained: ISSQN retained by the tomador (tpRetISSQN=2) instead
  of the issuer (tpRetISSQN=1).
- observations: free-text note on the service (xInfComp).

The platform only issues the first item per call — each variant
below is issued in its own `client.issue()` call, not batched."""

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
    """Builds Product examples for NFSE, one field variation each."""

    @staticmethod
    def basic():
        """Only description/amount — service_code falls back to the
        company's fiscal profile."""
        return Product(description="Software development", amount=5000.00)

    @staticmethod
    def with_service_code():
        """Explicit service_code, overriding the company default —
        1.06 (Assessoria e consultoria em informática)."""
        return Product(
            description="Technical consulting - 10 hours",
            amount=1500.00,
            service_code="1.06",
        )

    @staticmethod
    def with_discount():
        """An unconditional discount applied to the service value."""
        return Product(
            description="Monthly support and maintenance",
            amount=800.00,
            service_code="1.07",
            service_discount=50.00,
        )

    @staticmethod
    def with_tax_retained():
        """ISSQN retained by the tomador instead of the issuer."""
        return Product(
            description="UI/UX design",
            amount=3200.00,
            service_code="1.03",
            tax_retained=True,
        )

    @staticmethod
    def with_observations():
        """A free-text note attached to the service."""
        return Product(
            description="Systems analysis and development",
            amount=2400.00,
            service_code="1.01",
            observations="Referente ao contrato #2026-0042, etapa 2 de 3.",
        )

    @staticmethod
    def full():
        """Every optional field set at once."""
        return Product(
            description="Software licensing",
            amount=1200.00,
            service_code="1.05",
            service_discount=100.00,
            tax_retained=True,
            observations="Licenca anual, renovacao automatica.",
        )

    @classmethod
    def all(cls):
        return [
            cls.basic(),
            cls.with_service_code(),
            cls.with_discount(),
            cls.with_tax_retained(),
            cls.with_observations(),
            cls.full(),
        ]


def issue(client, item):
    try:
        result = client.issue(
            document_type=DocumentType.NFSE,
            client_name="Comprador Teste Ltda",
            tax_id="11222333000181",
            items=[item],
        )
    except ConnectionFailedError:
        print("Could not reach the platform")
        return None
    except APIError as error:
        print(f"Request rejected ({error.status_code}): "
              f"{error.detail}")
        return None

    print("Issued:", result)
    return result


def main():
    client = Invoice(api_key=os.environ.get("NFE_TEST_API_KEY"))
    for item in ServiceCatalog.all():
        print(f"--- {item.description} ---")
        issue(client, item)


if __name__ == "__main__":
    main()
