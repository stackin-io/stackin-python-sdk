#!/usr/bin/env python
"""How to look up a fiscal document by its access key with the Stackin SDK."""

import os
import sys

from dotenv import load_dotenv

from stackin import APIError, ConnectionFailedError, DocumentType, Invoice

load_dotenv()


def main():
    if len(sys.argv) < 3:
        print("Usage: python consult_invoice.py <access_key> <nfe|nfse>")
        return
    access_key, document_type = sys.argv[1], DocumentType(sys.argv[2])

    client = Invoice(api_key=os.environ.get("NFE_TEST_API_KEY"))
    try:
        result = client.consult(access_key, document_type=document_type)
    except ConnectionFailedError:
        print("Could not reach the platform")
        return
    except APIError as error:
        print(f"Request rejected ({error.status_code}): {error.detail}")
        return

    print("Status:", result)


if __name__ == "__main__":
    main()
