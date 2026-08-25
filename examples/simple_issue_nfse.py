#!/usr/bin/env python

from invoice import (
    Address,
    APIError,
    ConnectionFailedError,
    DocumentType,
    Invoice,
)


def main():
    client = Invoice(base_url="http://localhost:8000")

    try:
        return client.issue(
            document_type=DocumentType.NFSE,
            client_name="John Doe",
            tax_id="00000000000",
            description="Software development",
            amount=5000.00,
            address=Address(city_code="4106902"),
        )
    except ConnectionFailedError:
        print("invoice-api is not running on localhost:8000")
        return None
    except APIError as error:
        print(f"invoice-api rejected the request ({error.status_code}): "
              f"{error.detail}")
        return None


if __name__ == "__main__":
    main()
