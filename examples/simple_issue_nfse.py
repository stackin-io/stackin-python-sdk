#!/usr/bin/env python
"""Minimal NFSE issuance — the only NFSE-specific field
invoice-api requires is address.city_code (IBGE code of where the
service is provided, cLocPrestacao). No Product here — NCM/CFOP
don't apply to a service.

Note: NFSE's signature algorithm is genuinely unconfirmed (see
plan/IMPLEMENTATION.md section 10), so this example is expected to
get a 501 from invoice-api today, not a successful issuance."""

from invoice import (
    Address,
    APIError,
    ConnectionFailedError,
    DocumentType,
    Invoice,
)


def main():
    client = Invoice(base_url="http://localhost:8000")

    try:
        result = client.issue(
            document_type=DocumentType.NFSE,
            client_name="John Doe",
            tax_id="00000000000",
            description="Software development",
            amount=5000.00,
            address=Address(city_code="4106902"),
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
