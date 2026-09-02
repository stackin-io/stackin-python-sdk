#!/usr/bin/env python
"""How to retry a previously issued invoice with the Stackin SDK."""

import os
import sys

from dotenv import load_dotenv

from stackin import APIError, ConnectionFailedError, Invoice

load_dotenv()


def main():
    invoice_id = (
        sys.argv[1] if len(sys.argv) > 1 else os.environ.get("INVOICE_ID")
    )
    if not invoice_id:
        print("Usage: python reissue_invoice.py <invoice_id>")
        return

    client = Invoice(api_key=os.environ.get("NFE_TEST_API_KEY"))
    try:
        result = client.reissue(invoice_id)
    except ConnectionFailedError:
        print("Could not reach the platform")
        return
    except APIError as error:
        print(f"Request rejected ({error.status_code}): {error.detail}")
        return

    print("Reissued:", result)


if __name__ == "__main__":
    main()
