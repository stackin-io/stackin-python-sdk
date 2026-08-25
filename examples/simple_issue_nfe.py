#!/usr/bin/env python

from invoice import Address, ConnectionFailedError, DocumentType, Invoice


def main():
    client = Invoice(base_url="http://localhost:8000")

    try:
        return client.issue(
            document_type=DocumentType.NFE,
            client_name="Buyer Company Ltd",
            tax_id="11111111111111",
            description="Test product",
            amount=100.00,
            address=Address(state="SP"),
        )
    except ConnectionFailedError:
        print("invoice-api is not running on localhost:8000")
        return None


if __name__ == "__main__":
    main()
