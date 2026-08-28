#!/usr/bin/env python
"""Minimal NFE issuance — every field here is required by
invoice-api for document_type=NFE:

- api_key: the issuing company's key (POST /api/v1/companies) —
  invoice-api resolves the issuer's UF/address/certificate from it.
- items: always a list, one Product even for a single item.
- Product.ncm/Product.cfop: required XSD fields (tax classification/
  operation code), no NFE-valid default exists for either.
- recipient_address.state: optional, but sets idDest correctly
  (interstate vs internal) — omitting it always produces idDest=1.

Everything else (issuer data, access key, XML-DSig signature, tax
totals) is resolved server-side — see invoice-api/README.md."""

from invoice import (
    Address,
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
            document_type=DocumentType.NFE,
            client_name="Buyer Company Ltd",
            tax_id="11111111111111",
            items=[Product(description="Test product", amount=100.00, ncm="84713012", cfop="5102")],
            recipient_address=Address(state="RJ"),
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
