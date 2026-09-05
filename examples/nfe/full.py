import os

from dotenv import load_dotenv

from stackin import Address, DocumentType, Invoice
from stackin.br import PresumedCredit, Product

load_dotenv()


def main():
    client = Invoice(api_key=os.environ.get("STACKIN_API_KEY"))

    product = Product(
        description="Produto completo - todos os campos",
        amount=999.99,
        ncm="84713012",
        cfop="5102",
        unit="UN",
        quantity=2,
        barcode="7891000100103",
        cest="0300700",
        nve_codes=["NV0001", "NV0002"],
        ind_escala="N",
        manufacturer_cnpj="12345678000195",
        tax_benefit_code="PR820001",
        presumed_credits=[
            PresumedCredit(code="PR820001", percentage=3.0, amount=30.00),
        ],
        ex_tipi="01",
        freight=20.00,
        insurance=8.00,
        discount=15.00,
        other_expenses=5.00,
        used_movable_asset=False,
        purchase_order="PC-2026-00042",
        purchase_order_item="1",
        import_content_control_number="550E8400-E29B-41D4-A716-446655440000",
        recopi_number="00000000000012345678",
        extra_groups={},
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
