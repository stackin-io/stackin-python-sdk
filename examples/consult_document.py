#!/usr/bin/env python
"""Consult a previously issued document by access key. Set
NFE_TEST_ACCESS_KEY."""

import os

from dotenv import load_dotenv

from invoice import APIError, ConnectionFailedError, DocumentType, Invoice

load_dotenv()


def main():
    access_key = os.environ.get("NFE_TEST_ACCESS_KEY")

    client = Invoice(
        base_url="http://localhost:8000",
        api_key=os.environ.get("NFE_TEST_API_KEY"),
    )

    try:
        result = client.consult(access_key, document_type=DocumentType.NFE)
    except ConnectionFailedError:
        print("invoice-api is not running on localhost:8000")
        return None
    except APIError as error:
        print(f"invoice-api rejected the request ({error.status_code}): {error.detail}")
        return None

    print("Status:", result)
    return result


if __name__ == "__main__":
    main()
