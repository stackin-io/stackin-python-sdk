import os

from dotenv import load_dotenv

from stackin import Address, DocumentType, Invoice
from stackin.br import CofinsNt, IcmsSn900, IcmsUfDest, PisNt, Product, Tax

load_dotenv()


def main():
    client = Invoice(api_key=os.environ.get("STACKIN_API_KEY"))

    product = Product(
        description="Urso de Pelucia Dudu",
        amount=92.72,
        ncm="95030031",
        cfop="6108",
        freight=9.12,
        tax=Tax(
            icms=IcmsSn900(
                orig="0",
                csosn="900",
                mod_bc="3",
                v_bc="101.84",
                p_icms="12.0000",
                v_icms="12.22",
            ),
            icms_uf_dest=IcmsUfDest(
                v_bc_uf_dest="101.84",
                p_icms_uf_dest="17.0000",
                p_icms_inter="12.00",
                p_icms_inter_part="100.0000",
                v_icms_uf_dest="5.09",
                v_icms_uf_remet="0.00",
            ),
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
