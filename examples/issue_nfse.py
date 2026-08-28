#!/usr/bin/env python
"""NFSe (service invoice, national ADN) — a single service, no
NCM/CFOP/product data (that's NFe-only). Needs an NFSe-configured
company's API key in NFSE_TEST_API_KEY."""

import os

from dotenv import load_dotenv

from invoice import APIError, ConnectionFailedError, DocumentType, Invoice
from invoice.br import Product

load_dotenv()


def main():
    client = Invoice(
        base_url="http://localhost:8000",
        api_key=os.environ.get("NFSE_TEST_API_KEY"),
    )

    try:
        result = client.issue(
            document_type=DocumentType.NFSE,
            client_name="Cliente de Serviço Ltda",
            tax_id="33444555000122",
            items=[
                Product(description="Consultoria em desenvolvimento de software", amount=8000.00)
            ],
        )
    except ConnectionFailedError:
        print("invoice-api is not running on localhost:8000")
        return None
    except APIError as error:
        print(f"invoice-api rejected the request ({error.status_code}): {error.detail}")
        return None

    print("Issued:", result)
    return result


if __name__ == "__main__":
    main()
