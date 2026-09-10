#!/usr/bin/env python
"""How to look up who a CNPJ belongs to before invoicing it."""

import os

from dotenv import load_dotenv

from stackin import APIError, ConnectionFailedError, Taxpayer

load_dotenv()

TAX_ID = "00000000000191"


def main():
    client = Taxpayer(api_key=os.environ.get("STACKIN_API_KEY"))

    try:
        found = client.get(TAX_ID)
    except ConnectionFailedError:
        print("Could not reach the platform")
        return
    except APIError as error:
        if error.status_code == 404:
            print(
                "The registry has no record of this tax id yet. It reloads "
                "monthly, so a recently registered company is simply not in "
                "it — this is not proof the company does not exist, and it "
                "is not a validation rule."
            )
            return
        print(f"Request rejected ({error.status_code}): {error.detail}")
        return

    print("Name:", found["name"])
    print("Trade name:", found["trade_name"])
    print("City code:", found["city_code"], "State:", found["state"])


if __name__ == "__main__":
    main()
