import os

from stackin import (
    Address,
    APIError,
    ConnectionFailedError,
    DocumentType,
    Invoice,
)

TOMADOR_ADDRESS = {
    "street": "Rua das Flores",
    "number": "123",
    "neighborhood": "Centro",
    "city": "Sao Paulo",
    "state": "SP",
    "zip_code": "01310100",
    "city_code": "3550308",
}


def issue(product, recipient_address=None):
    client = Invoice(api_key=os.environ.get("NFE_TEST_API_KEY"))
    try:
        result = client.issue(
            document_type=DocumentType.NFSE,
            client_name="Comprador Teste Ltda",
            tax_id="11222333000181",
            items=[product],
            recipient_address=Address(**recipient_address)
            if recipient_address
            else None,
        )
    except ConnectionFailedError:
        print("Could not reach the platform")
        return None
    except APIError as error:
        print(f"Request rejected ({error.status_code}): {error.detail}")
        return None

    print("Issued:", result)
    return result
