#!/usr/bin/env python
"""NFe using the extended `Product` fields (`det/prod`'s common
optional group) — real barcode, CEST, freight/insurance/discount,
purchase order tracking, and a presumed ICMS credit."""

import os

from dotenv import load_dotenv

from invoice import Address, APIError, ConnectionFailedError, DocumentType, Invoice
from invoice.br import PresumedCredit, Product

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
                    description="Smartphone com substituição tributária",
                    amount=1800.00,
                    ncm="85171231",
                    cfop="5405",
                    barcode="7891234567895",
                    cest="2104700",
                    freight=25.00,
                    insurance=5.00,
                    discount=50.00,
                    purchase_order="PED-2026-001",
                    purchase_order_item="1",
                    presumed_credits=[
                        PresumedCredit(code="SC010203", percentage=3.0, amount=54.0)
                    ],
                )
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
