#!/usr/bin/env python
"""NFe to a foreign recipient — `recipient_address.state="EX"` (the
standard `TUf` literal for a foreign recipient) makes `idDest`
"3-Foreign"."""

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
            client_name="Foreign Buyer Inc",
            tax_id="00000000000000",
            items=[
                Product(
                    description="Produto para exportação",
                    amount=1200.00,
                    ncm="84713012",
                    cfop="7102",
                )
            ],
            recipient_address=Address(state="EX"),
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
