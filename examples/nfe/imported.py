#!/usr/bin/env python
"""An imported item, tracked by its Ficha de Conteudo de Importacao."""

from _common import SAME_STATE_ADDRESS, issue
from dotenv import load_dotenv

from stackin import Address
from stackin.br import Product

load_dotenv()


def main():
    product = Product(
        description="Produto importado",
        amount=320.00,
        ncm="85171231",
        cfop="5102",
        ex_tipi="01",
        import_content_control_number="550E8400-E29B-41D4-A716-446655440000",
    )
    issue(product, Address(**SAME_STATE_ADDRESS))


if __name__ == "__main__":
    main()
