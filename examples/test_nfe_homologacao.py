#!/usr/bin/env python
"""Ready-to-run NFe issuance against SEFAZ homologação, for the
"NFe Homologacao Test" company (SC/SVRS) created for this test —
see invoice_api/app/core/database (Company 786e6800-8cad-4fa6-b5b0-
d0fe52fa0c28). Before running: fill in that company's Certificate
(.pfx path + password) via the console UI, and set NFE_TEST_API_KEY
to a token generated from that company's API Tokens page — nothing
else to set up.
"""

import os

from dotenv import load_dotenv

from invoice import (
    Address,
    APIError,
    ConnectionFailedError,
    DocumentType,
    Invoice,
)
from invoice.br import Product

load_dotenv()


def main():
    client = Invoice(
        base_url="http://localhost:8000",
        api_key=os.environ.get("NFE_TEST_API_KEY")
    )

    try:
        result = client.issue(
            document_type=DocumentType.NFE,
            client_name="Comprador Teste Ltda",
            tax_id="11222333000181",
            items=[
                Product(
                    description="Produto de teste - homologacao",
                    amount=100.00,
                    ncm="84713012",
                    cfop="5102",
                )
            ],
            recipient_address=Address(state="SC"),
        )
    except ConnectionFailedError:
        print("invoice-api is not running on localhost:8000")
        return None
    except APIError as error:
        print(
            f"invoice-api rejected the request ({error.status_code}): "
            f"{error.detail}"
        )
        return None

    print("Issued:", result)
    return result


if __name__ == "__main__":
    main()
