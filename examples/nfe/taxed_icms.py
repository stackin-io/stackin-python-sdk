import os

from dotenv import load_dotenv

from stackin import Address, DocumentType, Invoice
from stackin.br import CofinsAliq, IcmsSn102, PisAliq, Product, Tax

load_dotenv()


def main():
    client = Invoice(api_key=os.environ.get("STACKIN_API_KEY"))

    product = Product(
        description="Plastico celofane 50x50",
        amount=0.27,
        ncm="39202019",
        cfop="6108",
        freight=0.03,
        tax=Tax(
            icms=IcmsSn102(orig="0", csosn="102"),
            pis=PisAliq(cst="01", v_bc="0.30", p_pis="0.6500", v_pis="0.00"),
            cofins=CofinsAliq(
                cst="01", v_bc="0.30", p_cofins="3.0000", v_cofins="0.01"
            ),
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
