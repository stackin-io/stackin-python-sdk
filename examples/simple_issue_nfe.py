#!/usr/bin/env python
"""Minimal NFE issuance — every field here is required by
invoice-api for document_type=NFE:

- api_key: the issuing company's key (POST /api/v1/companies) —
  invoice-api resolves the issuer's UF/address/certificate from it.
- items: always a list, one Product even for a single item.
- Product.ncm/Product.cfop: required XSD fields (tax classification/
  operation code), no NFE-valid default exists for either.
- recipient_address.state: optional, but sets idDest correctly
  (interstate vs internal) — omitting it always produces idDest=1.

Everything else (issuer data, access key, XML-DSig signature, tax
totals) is resolved server-side — see invoice-api/README.md."""

import os

from dotenv import load_dotenv

from invoice import (
    Address,
    APIError,
    ConnectionFailedError,
    DocumentType,
    Invoice,
)
from invoice.br import PresumedCredit, Product

load_dotenv()


class ProductCatalog:
    """Builds Product examples, from the bare minimum to every field filled."""

    @staticmethod
    def basic():
        """Only what NFE requires: description, amount, ncm, cfop."""
        return Product(
            description="Produto basico",
            amount=50.00,
            ncm="84713012",
            cfop="5102",
        )

    @staticmethod
    def with_quantity():
        """Multiple units at a per-unit price."""
        return Product(
            description="Caixa de parafusos",
            amount=12.50,
            ncm="73181500",
            cfop="5102",
            unit="CX",
            quantity=20,
        )

    @staticmethod
    def with_barcode():
        """A real GTIN/EAN instead of the "SEM GTIN" default."""
        return Product(
            description="Produto com codigo de barras",
            amount=29.90,
            ncm="21069090",
            cfop="5102",
            barcode="7891000100103",
        )

    @staticmethod
    def with_tax_benefit():
        """ICMS-ST item with a state tax benefit and presumed credit."""
        return Product(
            description="Produto com beneficio fiscal",
            amount=80.00,
            ncm="22021000",
            cfop="5102",
            cest="0300700",
            tax_benefit_code="PR820001",
            presumed_credits=[
                PresumedCredit(code="PR001", percentage=3.0, amount=2.40),
            ],
        )

    @staticmethod
    def scale_manufactured():
        """Relevant-scale manufacturing indicator and its manufacturer CNPJ."""
        return Product(
            description="Produto de fabricacao em escala",
            amount=150.00,
            ncm="87141000",
            cfop="5102",
            ind_escala="N",
            manufacturer_cnpj="12345678000199",
        )

    @staticmethod
    def with_extra_charges():
        """Freight, insurance, discount, and other expenses on the item."""
        return Product(
            description="Produto com encargos adicionais",
            amount=200.00,
            ncm="94036000",
            cfop="5102",
            freight=15.00,
            insurance=5.00,
            discount=10.00,
            other_expenses=3.50,
        )

    @staticmethod
    def used_asset():
        """A used movable asset being resold."""
        return Product(
            description="Bem movel usado",
            amount=500.00,
            ncm="87032310",
            cfop="5102",
            used_movable_asset=True,
        )

    @staticmethod
    def with_purchase_order():
        """Linked to the buyer's purchase order and item number."""
        return Product(
            description="Produto vinculado a pedido de compra",
            amount=75.00,
            ncm="84433210",
            cfop="5102",
            purchase_order="PC-2026-00042",
            purchase_order_item="1",
        )

    @staticmethod
    def imported():
        """An imported item, tracked by its Ficha de Conteudo de Importacao."""
        return Product(
            description="Produto importado",
            amount=320.00,
            ncm="85171231",
            cfop="5102",
            ex_tipi="01",
            import_content_control_number="1234567890123",
        )

    @staticmethod
    def full():
        """Every field on Product filled in at once."""
        return Product(
            description="Produto completo - todos os campos",
            amount=999.99,
            ncm="84713012",
            cfop="5102",
            unit="UN",
            quantity=2,
            barcode="7891000100103",
            cest="0300700",
            nve_codes=["NV0001", "NV0002"],
            ind_escala="S",
            manufacturer_cnpj="12345678000199",
            tax_benefit_code="PR820001",
            presumed_credits=[
                PresumedCredit(code="PR001", percentage=3.0, amount=30.00),
            ],
            ex_tipi="01",
            freight=20.00,
            insurance=8.00,
            discount=15.00,
            other_expenses=5.00,
            used_movable_asset=False,
            purchase_order="PC-2026-00042",
            purchase_order_item="1",
            import_content_control_number="1234567890123",
            recopi_number="00012345",
            extra_groups={},
        )

    @classmethod
    def all(cls):
        """One instance of every product variant above."""
        return [
            cls.basic(),
            cls.with_quantity(),
            cls.with_barcode(),
            cls.with_tax_benefit(),
            cls.scale_manufactured(),
            cls.with_extra_charges(),
            cls.used_asset(),
            cls.with_purchase_order(),
            cls.imported(),
            cls.full(),
        ]


def main():
    client = Invoice(
        base_url="http://localhost:8000",
        api_key=os.environ.get("NFE_TEST_API_KEY")
    )

    try:
        result = client.issue(
            document_type=DocumentType.NFE,
            client_name="Comprador Teste Ltda",
            tax_id="11222333000181",
            items=ProductCatalog.all(),
            recipient_address=Address(state="SC"),
        )
    except ConnectionFailedError:
        print("invoice-api is not running on localhost:8000")
        return None
    except APIError as error:
        print(f"invoice-api rejected the request ({error.status_code}): "
              f"{error.detail}")
        return None

    print("Issued:", result)
    return result


if __name__ == "__main__":
    main()
