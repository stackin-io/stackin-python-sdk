import os

from dotenv import load_dotenv

from stackin import Address, DocumentType, Invoice
from stackin.br import PresumedCredit, Product

load_dotenv()


def main():
    client = Invoice(api_key=os.environ.get("STACKIN_API_KEY"))

    product = Product(
        description="Produto com beneficio fiscal",
        amount=80.00,
        ncm="22021000",
        cfop="5102",
        cest="0300700",
        tax_benefit_code="PR820001",
        presumed_credits=[
            PresumedCredit(code="PR820001", percentage=3.0, amount=2.40),
        ],
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
