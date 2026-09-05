import os

from dotenv import load_dotenv

from stackin import DocumentType, Invoice
from stackin.br import Product

load_dotenv()


def main():
    client = Invoice(api_key=os.environ.get("STACKIN_API_KEY"))

    product = Product(
        description="Software development",
        amount=5000.00,
    )

    result = client.issue(
        document_type=DocumentType.NFSE,
        client_name="Comprador Teste Ltda",
        tax_id="11222333000181",
        items=[product],
    )

    print(result)


if __name__ == "__main__":
    main()
