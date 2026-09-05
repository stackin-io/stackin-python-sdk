import os

from dotenv import load_dotenv

from stackin import Address, DocumentType, Invoice
from stackin.br import Product

load_dotenv()


def main():
    client = Invoice(api_key=os.environ.get("STACKIN_API_KEY"))

    product = Product(
        description="UI/UX design",
        amount=3200.00,
        service_code="1.03",
        tax_retained=True,
    )

    result = client.issue(
        document_type=DocumentType.NFSE,
        client_name="Comprador Teste Ltda",
        tax_id="11222333000181",
        items=[product],
        recipient_address=Address(
            street="Rua das Flores",
            number="123",
            neighborhood="Centro",
            city="Sao Paulo",
            state="SP",
            zip_code="01310100",
            city_code="3550308",
        ),
    )

    print(result)


if __name__ == "__main__":
    main()
