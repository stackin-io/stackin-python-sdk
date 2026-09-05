#!/usr/bin/env python
"""How to cancel a previously issued fiscal document with the Stackin SDK."""

import os

from dotenv import load_dotenv

from stackin import APIError, ConnectionFailedError, DocumentType, Invoice

load_dotenv()

ACCESS_KEY = "42250611222333000181550010000000011000000017"
DOCUMENT_TYPE = DocumentType.NFE
REASON = "Emitida com dados incorretos do destinatario"


def main():
    client = Invoice(api_key=os.environ.get("STACKIN_API_KEY"))
    try:
        result = client.cancel(
            ACCESS_KEY, document_type=DOCUMENT_TYPE, reason=REASON
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
