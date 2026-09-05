#!/usr/bin/env python
"""How to retry a previously issued invoice with the Stackin SDK."""

import os

from dotenv import load_dotenv

from stackin import APIError, ConnectionFailedError, Invoice

load_dotenv()

INVOICE_ID = "00000000-0000-0000-0000-000000000000"


def main():
    client = Invoice(api_key=os.environ.get("STACKIN_API_KEY"))
    try:
        result = client.reissue(INVOICE_ID)
    except ConnectionFailedError:
        print("Could not reach the platform")
        return
    except APIError as error:
        print(f"Request rejected ({error.status_code}): {error.detail}")
        return

    print("Reissued:", result)


if __name__ == "__main__":
    main()
