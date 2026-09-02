#!/usr/bin/env python
"""How to cancel a previously issued fiscal document with the Stackin SDK."""

import os
import sys

from dotenv import load_dotenv

from stackin import APIError, ConnectionFailedError, DocumentType, Invoice

load_dotenv()


def main():
    if len(sys.argv) < 4:
        print(
            "Usage: python cancel_invoice.py <access_key> <nfe|nfse> <reason>"
        )
        return
    access_key, document_type, reason = (
        sys.argv[1],
        DocumentType(sys.argv[2]),
        sys.argv[3],
    )

    client = Invoice(api_key=os.environ.get("NFE_TEST_API_KEY"))
    try:
        result = client.cancel(
            access_key, document_type=document_type, reason=reason
        )
    except ConnectionFailedError:
        print("Could not reach the platform")
        return
    except APIError as error:
        print(f"Request rejected ({error.status_code}): {error.detail}")
        return

    print("Cancelled:", result)


if __name__ == "__main__":
    main()
