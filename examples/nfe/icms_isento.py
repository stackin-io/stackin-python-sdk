import os

from dotenv import load_dotenv

from stackin import Address, DocumentType, Invoice
from stackin.br import CofinsNt, IcmsSn102, PisNt, Product, Tax

load_dotenv()


def main():
    client = Invoice(api_key=os.environ.get("STACKIN_API_KEY"))

    product = Product(
        description="Rosa Holambra Vermelha",
        amount=112.44,
        ncm="06031100",
        cfop="6108",
        quantity=6,
        freight=11.05,
        tax=Tax(
            icms=IcmsSn102(orig="0", csosn="400"),
            pis=PisNt(cst="07"),
            cofins=CofinsNt(cst="07"),
        ),
    )

    result = client.issue(
        document_type=DocumentType.NFE,
        client_name="Comprador Teste Ltda",
        tax_id="11222333000181",
        items=[product],
        recipient_address=Address(
            street="Avenida Atlantica",
            number="500",
            neighborhood="Copacabana",
            city="Rio de Janeiro",
            state="RJ",
            zip_code="22010000",
            city_code="3304557",
        ),
    )

    print(result)


if __name__ == "__main__":
    main()
