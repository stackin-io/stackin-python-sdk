import os

from stackin import APIError, ConnectionFailedError, DocumentType, Invoice

SAME_STATE_ADDRESS = {
    "street": "Rua das Palmeiras",
    "number": "100",
    "neighborhood": "Centro",
    "city": "Florianopolis",
    "state": "SC",
    "zip_code": "88010000",
    "city_code": "4205407",
}

OTHER_STATE_ADDRESS = {
    "street": "Avenida Atlantica",
    "number": "500",
    "neighborhood": "Copacabana",
    "city": "Rio de Janeiro",
    "state": "RJ",
    "zip_code": "22010000",
    "city_code": "3304557",
}


def issue(product, recipient_address):
    client = Invoice(api_key=os.environ.get("NFE_TEST_API_KEY"))
    try:
        result = client.issue(
            document_type=DocumentType.NFE,
            client_name="Comprador Teste Ltda",
            tax_id="11222333000181",
            items=[product],
            recipient_address=recipient_address,
        )
    except ConnectionFailedError:
        print("Could not reach the platform")
        return None
    except APIError as error:
        print(f"Request rejected ({error.status_code}): {error.detail}")
        return None

    print("Issued:", result)
    return result
