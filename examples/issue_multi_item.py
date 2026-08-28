#!/usr/bin/env python
"""NFe with more than one product on the same document — `items` with
several `Product` entries. Same company/setup as
`test_nfe_homologacao.py`."""

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
            client_name="Comprador Teste Ltda",
            tax_id="11222333000181",
            items=[
                Product(
                    description="Notebook",
                    amount=3500.00,
                    ncm="84713012",
                    cfop="5102",
                    quantity=1.0,
                ),
                Product(
                    description="Mouse sem fio",
                    amount=80.00,
                    ncm="84716053",
                    cfop="5102",
                    quantity=2.0,
                ),
                Product(
                    description="Teclado mecânico",
                    amount=250.00,
                    ncm="84716060",
                    cfop="5102",
                    quantity=1.0,
                ),
            ],
            recipient_address=Address(state="SC"),
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
