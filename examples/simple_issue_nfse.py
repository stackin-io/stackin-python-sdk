#!/usr/bin/env python
"""Minimal NFSE issuance — `api_key` (the issuing company's key,
POST /api/v1/companies) is the only thing invoice-api needs to
resolve the issuer's city/certificate. No Product here — NCM/CFOP
don't apply to a service.

Note: NFSE's signature algorithm is genuinely unconfirmed (see
plan/IMPLEMENTATION.md section 10), so this example is expected to
get a 501 from invoice-api today, not a successful issuance."""

from invoice import (
    APIError,
    ConnectionFailedError,
    DocumentType,
    Invoice,
)
from invoice.br import Product


def main():
    client = Invoice(
        base_url="http://localhost:8000",
        api_key="COMPANY_API_KEY"
    )

    try:
        result = client.issue(
            document_type=DocumentType.NFSE,
            client_name="John Doe",
            tax_id="00000000000",
            items=[Product(description="Software development", amount=5000.00)],
        )
    except ConnectionFailedError:
        print("invoice-api is not running on localhost:8000")
        return None
    except APIError as error:
        print(f"invoice-api rejected the request ({error.status_code}): "
              f"{error.detail}")
        return None

    print("Issued:", result)
    return result


if __name__ == "__main__":
    main()
