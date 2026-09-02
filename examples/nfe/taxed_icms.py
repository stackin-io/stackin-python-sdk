#!/usr/bin/env python
"""CSOSN 102 (no credit) — MEI/Simples equivalent of ICMS00."""

from _common import OTHER_STATE_ADDRESS, issue
from dotenv import load_dotenv

from stackin import Address
from stackin.br import CofinsAliq, IcmsSn102, PisAliq, Product, Tax

load_dotenv()

if __name__ == "__main__":
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
    issue(product, Address(**OTHER_STATE_ADDRESS))
