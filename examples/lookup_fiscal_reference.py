#!/usr/bin/env python
"""How to resolve an NCM, and how to find one you only half remember."""

import os

from dotenv import load_dotenv

from stackin import APIError, ConnectionFailedError, FiscalReference

load_dotenv()

NCM_CODE = "84716052"
SEARCH_TERM = "teclado"


def main():
    client = FiscalReference(api_key=os.environ.get("STACKIN_API_KEY"))

    try:
        ncm = client.ncm.get(NCM_CODE)
        print("NCM:", ncm["description"])
        print("Extras:", ncm["metadata"])

        found = client.ncm.search(SEARCH_TERM, limit=5)
        print(f"\n{found['total']} match '{SEARCH_TERM}'; first page:")
        for row in found["data"]:
            print(" ", row["code"], row["description"])

        print("\nClassifications available:", client.kinds())

        print("Any kind by name:", client.kind("cfop").get("5102"))
    except ConnectionFailedError:
        print("Could not reach the platform")
    except APIError as error:
        print(f"Request rejected ({error.status_code}): {error.detail}")


if __name__ == "__main__":
    main()
