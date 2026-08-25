#!/usr/bin/env python
"""Argentina (WSFEv1) — wired end to end, but expected to fail today.

invoice-api routes document_type=FACTURA through app/providers/ar/wsfe/
(ARCA), a scaffold with no confirmed WSAA/WSFEv1 host (see
invoice-api/plan/ARGENTINA.md) — Config refuses to build, so this
call gets a 400 explaining exactly that. Not a bug: the same honest
wall NFe hit before MOC 7.0 was downloaded, and NFSe still hits for
its signature algorithm."""

from invoice import (
    Address,
    APIError,
    ConnectionFailedError,
    DocumentType,
    Invoice,
)
from invoice.ar import InvoiceClass, InvoiceDocument


def main():
    client = Invoice(base_url="http://localhost:8000")

    try:
        result = client.issue(
            document_type=DocumentType.FACTURA,
            client_name="John Doe",
            tax_id="12345678901",
            description="Test product",
            amount=100.00,
            address=Address(),
            extra=InvoiceDocument(
                invoice_class=InvoiceClass.B,
                point_of_sale=1,
                customer_document="12345678",
                document_type="DNI",
            ),
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
