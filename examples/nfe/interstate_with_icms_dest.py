#!/usr/bin/env python
"""Interstate sale, partilha do ICMS — CSOSN 900 (MEI/Simples)."""

from _common import OTHER_STATE_ADDRESS, issue
from dotenv import load_dotenv

from stackin import Address
from stackin.br import CofinsNt, IcmsSn900, IcmsUfDest, PisNt, Product, Tax

load_dotenv()


def main():
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
    issue(product, Address(**OTHER_STATE_ADDRESS))


if __name__ == "__main__":
    main()
