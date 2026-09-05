import os

from dotenv import load_dotenv

from stackin import Address, DocumentType, Invoice
from stackin.br import Product

load_dotenv()


def main():
    client = Invoice(api_key=os.environ.get("STACKIN_API_KEY"))

    product = Product(
        description="Produto importado",
        amount=320.00,
        ncm="85171231",
        cfop="5102",
        ex_tipi="01",
        import_content_control_number="550E8400-E29B-41D4-A716-446655440000",
    )

    result = client.issue(
        document_type=DocumentType.NFE,
        client_name="Comprador Teste Ltda",
        tax_id="11222333000181",
        items=[product],
        recipient_address=Address(
            street="Rua das Palmeiras",
            number="100",
            neighborhood="Centro",
            city="Florianopolis",
            state="SC",
            zip_code="88010000",
            city_code="4205407",
        ),
    )

    print(result)


if __name__ == "__main__":
    main()
