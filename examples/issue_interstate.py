#!/usr/bin/env python
"""NFe to a recipient in a different state from the issuer —
`recipient_address.state` different from the issuer's own UF makes
`idDest` "2-Interstate" instead of "1-Internal"."""

import os

from dotenv import load_dotenv

from invoice import Address, APIError, ConnectionFailedError, DocumentType, Invoice
from invoice.br import Product

load_dotenv()


def main():
    client = Invoice(
        base_url="http://localhost:8000",
        api_key=os.environ.get("NFE_TEST_API_KEY"),
    )

    try:
        result = client.issue(
            document_type=DocumentType.NFE,
            client_name="Comprador de Outro Estado Ltda",
            tax_id="22333444000199",
            items=[
                Product(
                    description="Produto para venda interestadual",
                    amount=500.00,
                    ncm="84713012",
                    cfop="6102",
                )
            ],
            recipient_address=Address(state="SP"),
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
