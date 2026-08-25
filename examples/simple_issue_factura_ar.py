#!/usr/bin/env python
"""Argentina (WSFEv1) — scaffold, does NOT actually issue anything.

invoice-api has no DocumentType for Argentina yet (only "nfe"/"nfse"
exist, both Brazilian) — app/providers/ar/wsfe/ is a scaffold that
refuses to authorize (see invoice-api/plan/ARGENTINA.md, unconfirmed
WSAA/WSFEv1 sources). This example only builds the InvoiceDocument
that would go into Invoice.issue(document=...)'s slot once that's
real, so the intended shape is visible without pretending it works
today."""

import json

from invoice.ar import InvoiceClass, InvoiceDocument


def main():
    invoice_document = InvoiceDocument(
        invoice_class=InvoiceClass.B,
        point_of_sale=1,
        customer_document="12345678",
        document_type="DNI",
    )

    print("Would send (once invoice-api supports Argentina):")
    print(json.dumps(invoice_document.to_dict()))
    print(
        "\nNot calling Invoice.issue() — there's no DocumentType.AR to "
        "pass it. See invoice-api/plan/ARGENTINA.md for what's missing."
    )
    return invoice_document


if __name__ == "__main__":
    main()
