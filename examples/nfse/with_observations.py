import os

from dotenv import load_dotenv

from stackin import DocumentType, Invoice
from stackin.br import Product

load_dotenv()


def main():
    client = Invoice(api_key=os.environ.get("STACKIN_API_KEY"))

    product = Product(
        description="Systems analysis and development",
        amount=2400.00,
        service_code="1.01",
        observations="Referente ao contrato #2026-0042, etapa 2 de 3.",
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
