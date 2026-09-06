import unittest

from stackin.br import (
    CofinsAliq,
    CofinsNt,
    CofinsOutr,
    CofinsQtde,
    CofinsSt,
    Icms00,
    Icms02,
    Icms40,
    Icms60,
    IcmsPart,
    IcmsSn101,
    IcmsSn102,
    IcmsSn201,
    IcmsSn202,
    IcmsSn500,
    IcmsSn900,
    IcmsSt,
    IcmsUfDest,
    Ipi,
    IpiNt,
    IpiTrib,
    PisAliq,
    PisNt,
    PisOutr,
    PisQtde,
    PisSt,
    Tax,
)


class TestTaxToDict(unittest.TestCase):
    def test_empty_returns_empty_dict(self):
        self.assertEqual(Tax().to_dict(), {})

    def test_with_v_tot_trib(self):
        self.assertEqual(
            Tax(v_tot_trib="10.00").to_dict(), {"v_tot_trib": "10.00"}
        )

    def test_icms00_is_emitted_bare(self):
        tax = Tax(
            icms=Icms00(
                orig="0",
                mod_bc="3",
                v_bc="100.00",
                p_icms="18.0000",
                v_icms="18.00",
            )
        )
        data = tax.to_dict()
        self.assertEqual(data["icms"]["orig"], "0")
        self.assertEqual(data["icms"]["cst"], "00")
        self.assertEqual(data["icms"]["v_icms"], "18.00")

    def test_icms40_is_emitted_bare(self):
        tax = Tax(icms=Icms40(orig="0", cst="40"))
        self.assertEqual(tax.to_dict()["icms"], {"orig": "0", "cst": "40"})

    def test_icms60_is_emitted_bare(self):
        tax = Tax(icms=Icms60(orig="0"))
        self.assertEqual(tax.to_dict()["icms"], {"orig": "0", "cst": "60"})

    def test_icms_sn101_is_emitted_bare(self):
        tax = Tax(
            icms=IcmsSn101(orig="0", p_cred_sn="1.5000", v_cred_icms_sn="0.10")
        )
        data = tax.to_dict()
        self.assertEqual(data["icms"]["csosn"], "101")
        self.assertEqual(data["icms"]["p_cred_sn"], "1.5000")

    def test_icms_sn102_is_emitted_bare(self):
        tax = Tax(icms=IcmsSn102(orig="0", csosn="102"))
        self.assertEqual(tax.to_dict()["icms"], {"orig": "0", "csosn": "102"})

    def test_icms_sn900_is_emitted_bare(self):
        tax = Tax(
            icms=IcmsSn900(
                orig="0",
                csosn="900",
                mod_bc="3",
                v_bc="101.84",
                p_icms="12.0000",
                v_icms="12.22",
            )
        )
        data = tax.to_dict()
        self.assertEqual(data["icms"]["csosn"], "900")
        self.assertEqual(data["icms"]["v_icms"], "12.22")

    def test_icms_uf_dest(self):
        tax = Tax(
            icms_uf_dest=IcmsUfDest(
                v_bc_uf_dest="101.84",
                p_icms_uf_dest="17.0000",
                p_icms_inter="12.00",
                p_icms_inter_part="100.0000",
                v_icms_uf_dest="5.09",
                v_icms_uf_remet="0.00",
            )
        )
        data = tax.to_dict()
        self.assertEqual(data["icms_uf_dest"]["v_bc_uf_dest"], "101.84")
        self.assertEqual(data["icms_uf_dest"]["p_icms_inter"], "12.00")

    def test_ipi_keeps_the_variant_under_trib(self):
        tax = Tax(ipi=Ipi(c_enq="999", trib=IpiTrib(cst="00", v_ipi="0.00")))
        data = tax.to_dict()
        self.assertEqual(data["ipi"]["c_enq"], "999")
        self.assertEqual(data["ipi"]["trib"]["cst"], "00")

    def test_ipi_nt_variant(self):
        tax = Tax(ipi=Ipi(c_enq="999", trib=IpiNt(cst="53")))
        self.assertEqual(
            tax.to_dict()["ipi"], {"c_enq": "999", "trib": {"cst": "53"}}
        )

    def test_ipi_as_raw_dict_passed_through(self):
        tax = Tax(ipi={"c_enq": "999"})
        self.assertEqual(tax.to_dict()["ipi"], {"c_enq": "999"})

    def test_pis_aliq_is_emitted_bare(self):
        tax = Tax(
            pis=PisAliq(cst="01", v_bc="100.00", p_pis="0.6500", v_pis="0.65")
        )
        self.assertEqual(tax.to_dict()["pis"]["cst"], "01")

    def test_pis_nt_is_emitted_bare(self):
        tax = Tax(pis=PisNt(cst="07"))
        self.assertEqual(tax.to_dict()["pis"], {"cst": "07"})

    def test_pis_outr_is_emitted_bare(self):
        tax = Tax(pis=PisOutr(cst="99", v_pis="0.00"))
        self.assertEqual(tax.to_dict()["pis"], {"cst": "99", "v_pis": "0.00"})

    def test_cofins_aliq_is_emitted_bare(self):
        tax = Tax(
            cofins=CofinsAliq(
                cst="01", v_bc="100.00", p_cofins="3.0000", v_cofins="3.00"
            )
        )
        self.assertEqual(tax.to_dict()["cofins"]["cst"], "01")

    def test_cofins_nt_is_emitted_bare(self):
        tax = Tax(cofins=CofinsNt(cst="07"))
        self.assertEqual(tax.to_dict()["cofins"], {"cst": "07"})

    def test_cofins_outr_is_emitted_bare(self):
        tax = Tax(cofins=CofinsOutr(cst="99", v_cofins="0.00"))
        self.assertEqual(
            tax.to_dict()["cofins"],
            {"cst": "99", "v_cofins": "0.00"},
        )

    def test_full_combination(self):
        tax = Tax(
            v_tot_trib="1.00",
            icms=IcmsSn102(orig="0", csosn="102"),
            icms_uf_dest=IcmsUfDest(
                v_bc_uf_dest="1.00",
                p_icms_uf_dest="1.00",
                p_icms_inter="4.00",
                p_icms_inter_part="1.00",
                v_icms_uf_dest="1.00",
                v_icms_uf_remet="1.00",
            ),
            ipi=Ipi(c_enq="999", trib=IpiNt(cst="53")),
            pis=PisNt(cst="07"),
            cofins=CofinsNt(cst="07"),
        )
        data = tax.to_dict()
        self.assertEqual(
            set(data.keys()),
            {
                "v_tot_trib",
                "icms",
                "icms_uf_dest",
                "ipi",
                "pis",
                "cofins",
            },
        )


class TestTheCasingTheApiExpects(unittest.TestCase):
    """The API takes snake_case; the XSD spelling never leaves here."""

    def test_every_key_it_emits_is_snake_case(self):
        tax = Tax(
            v_tot_trib="1.00",
            icms=Icms00(
                orig="0",
                mod_bc="3",
                v_bc="100.00",
                p_icms="18.0000",
                v_icms="18.00",
            ),
            ipi=Ipi(c_enq="999", trib=IpiNt(cst="53")),
            pis=PisAliq(cst="01", v_bc="100.00", p_pis="1.65", v_pis="1.65"),
        )

        def keys(node):
            for key, value in node.items():
                yield key
                if isinstance(value, dict):
                    yield from keys(value)

        for key in keys(tax.to_dict()):
            with self.subTest(key):
                self.assertRegex(key, r"^[a-z][a-z0-9_]*$")

    def test_a_raw_dict_is_still_passed_through(self):
        tax = Tax(icms={"orig": "0", "csosn": "102"})

        self.assertEqual(tax.to_dict()["icms"], {"orig": "0", "csosn": "102"})


if __name__ == "__main__":
    unittest.main()


class TestTheGroupsTheLeiauteAddedLater(unittest.TestCase):
    """Monofasico, partilha, substituido and the Simples variants."""

    def test_a_monofasico_group_carries_its_own_fields(self):
        tax = Tax(
            icms=Icms02(orig="0", ad_rem_icms="0.1234", v_icms_mono="1.23")
        )

        self.assertEqual(
            tax.to_dict()["icms"],
            {
                "orig": "0",
                "cst": "02",
                "ad_rem_icms": "0.1234",
                "v_icms_mono": "1.23",
            },
        )

    def test_partilha_names_the_destination_state(self):
        tax = Tax(
            icms=IcmsPart(
                orig="0",
                cst="10",
                mod_bc="3",
                v_bc="100.00",
                p_icms="18.00",
                v_icms="18.00",
                mod_bc_st="4",
                v_bc_st="120.00",
                p_icms_st="18.00",
                v_icms_st="21.60",
                p_bc_op="100.0000",
                uf_st="RJ",
            )
        )
        group = tax.to_dict()["icms"]

        self.assertEqual(group["uf_st"], "RJ")
        self.assertEqual(group["p_bc_op"], "100.0000")

    def test_the_substituted_taxpayer_group_is_its_own_variant(self):
        tax = Tax(
            icms=IcmsSt(
                orig="0",
                cst="60",
                v_bc_st_ret="100.00",
                v_icms_st_ret="18.00",
                v_bc_st_dest="120.00",
                v_icms_st_dest="21.60",
            )
        )

        self.assertEqual(tax.to_dict()["icms"]["cst"], "60")

    def test_the_remaining_simples_variants_are_available(self):
        cases = {
            "201": IcmsSn201(
                orig="0",
                mod_bc_st="4",
                v_bc_st="120.00",
                p_icms_st="18.00",
                v_icms_st="21.60",
                p_cred_sn="2.50",
                v_cred_icms_sn="2.50",
            ),
            "202": IcmsSn202(
                orig="0",
                csosn="202",
                mod_bc_st="4",
                v_bc_st="120.00",
                p_icms_st="18.00",
                v_icms_st="21.60",
            ),
            "500": IcmsSn500(orig="0"),
        }

        for csosn, group in cases.items():
            with self.subTest(csosn):
                self.assertEqual(
                    Tax(icms=group).to_dict()["icms"]["csosn"], csosn
                )

    def test_pis_and_cofins_by_quantity_are_available(self):
        tax = Tax(
            pis=PisQtde(
                q_bc_prod="10.0000", v_aliq_prod="0.1000", v_pis="1.00"
            ),
            cofins=CofinsQtde(
                q_bc_prod="10.0000", v_aliq_prod="0.1000", v_cofins="1.00"
            ),
        )
        data = tax.to_dict()

        self.assertEqual(data["pis"]["cst"], "03")
        self.assertEqual(data["cofins"]["cst"], "03")

    def test_the_withheld_groups_sit_beside_their_own(self):
        tax = Tax(
            pis_st=PisSt(v_bc="100.00", p_pis="1.65", v_pis="1.65"),
            cofins_st=CofinsSt(
                v_bc="100.00", p_cofins="7.60", v_cofins="7.60"
            ),
        )
        data = tax.to_dict()

        self.assertEqual(data["pis_st"]["v_pis"], "1.65")
        self.assertEqual(data["cofins_st"]["v_cofins"], "7.60")

    def test_ipi_carries_the_stamp_fields_the_schema_allows(self):
        tax = Tax(
            ipi=Ipi(
                cnpj_prod="11222333000181",
                c_selo="001",
                q_selo="10",
                c_enq="999",
                trib=IpiNt(cst="53"),
            )
        )

        self.assertEqual(
            tax.to_dict()["ipi"],
            {
                "cnpj_prod": "11222333000181",
                "c_selo": "001",
                "q_selo": "10",
                "c_enq": "999",
                "trib": {"cst": "53"},
            },
        )
