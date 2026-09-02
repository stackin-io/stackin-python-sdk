import unittest

from stackin.br import (
    CofinsAliq,
    CofinsNt,
    CofinsOutr,
    Icms00,
    Icms40,
    Icms60,
    IcmsSn101,
    IcmsSn102,
    IcmsSn900,
    IcmsUfDest,
    Ipi,
    IpiNt,
    IpiTrib,
    PisAliq,
    PisNt,
    PisOutr,
    Tax,
)
from stackin.br.tax import _wrap


class TestTaxToDict(unittest.TestCase):
    def test_empty_returns_empty_dict(self):
        self.assertEqual(Tax().to_dict(), {})

    def test_with_v_tot_trib(self):
        self.assertEqual(
            Tax(v_tot_trib="10.00").to_dict(), {"vTotTrib": "10.00"}
        )

    def test_icms00_wrapped_by_tag(self):
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
        self.assertEqual(data["ICMS"]["ICMS00"]["orig"], "0")
        self.assertEqual(data["ICMS"]["ICMS00"]["CST"], "00")
        self.assertEqual(data["ICMS"]["ICMS00"]["vICMS"], "18.00")

    def test_icms40_wrapped_by_tag(self):
        tax = Tax(icms=Icms40(orig="0", cst="40"))
        self.assertEqual(
            tax.to_dict()["ICMS"], {"ICMS40": {"orig": "0", "CST": "40"}}
        )

    def test_icms60_wrapped_by_tag(self):
        tax = Tax(icms=Icms60(orig="0"))
        self.assertEqual(
            tax.to_dict()["ICMS"], {"ICMS60": {"orig": "0", "CST": "60"}}
        )

    def test_icms_sn101_wrapped_by_tag(self):
        tax = Tax(
            icms=IcmsSn101(orig="0", p_cred_sn="1.5000", v_cred_icms_sn="0.10")
        )
        data = tax.to_dict()
        self.assertEqual(data["ICMS"]["ICMSSN101"]["CSOSN"], "101")
        self.assertEqual(data["ICMS"]["ICMSSN101"]["pCredSN"], "1.5000")

    def test_icms_sn102_wrapped_by_tag(self):
        tax = Tax(icms=IcmsSn102(orig="0", csosn="102"))
        self.assertEqual(
            tax.to_dict()["ICMS"], {"ICMSSN102": {"orig": "0", "CSOSN": "102"}}
        )

    def test_icms_sn900_wrapped_by_tag(self):
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
        self.assertEqual(data["ICMS"]["ICMSSN900"]["CSOSN"], "900")
        self.assertEqual(data["ICMS"]["ICMSSN900"]["vICMS"], "12.22")

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
        self.assertEqual(data["ICMSUFDest"]["vBCUFDest"], "101.84")
        self.assertEqual(data["ICMSUFDest"]["pICMSInter"], "12.00")

    def test_ipi_typed_uses_ipi_to_dict(self):
        tax = Tax(ipi=Ipi(c_enq="999", trib=IpiTrib(cst="00", v_ipi="0.00")))
        data = tax.to_dict()
        self.assertEqual(data["IPI"]["cEnq"], "999")
        self.assertEqual(data["IPI"]["IPITrib"]["CST"], "00")

    def test_ipi_nt_variant(self):
        tax = Tax(ipi=Ipi(c_enq="999", trib=IpiNt(cst="53")))
        self.assertEqual(tax.to_dict()["IPI"]["IPINT"], {"CST": "53"})

    def test_ipi_as_raw_dict_passed_through(self):
        tax = Tax(ipi={"cEnq": "999"})
        self.assertEqual(tax.to_dict()["IPI"], {"cEnq": "999"})

    def test_pis_aliq_wrapped_by_tag(self):
        tax = Tax(
            pis=PisAliq(cst="01", v_bc="100.00", p_pis="0.6500", v_pis="0.65")
        )
        self.assertEqual(tax.to_dict()["PIS"]["PISAliq"]["CST"], "01")

    def test_pis_nt_wrapped_by_tag(self):
        tax = Tax(pis=PisNt(cst="07"))
        self.assertEqual(tax.to_dict()["PIS"], {"PISNT": {"CST": "07"}})

    def test_pis_outr_wrapped_by_tag(self):
        tax = Tax(pis=PisOutr(cst="99", v_pis="0.00"))
        self.assertEqual(
            tax.to_dict()["PIS"], {"PISOutr": {"CST": "99", "vPIS": "0.00"}}
        )

    def test_cofins_aliq_wrapped_by_tag(self):
        tax = Tax(
            cofins=CofinsAliq(
                cst="01", v_bc="100.00", p_cofins="3.0000", v_cofins="3.00"
            )
        )
        self.assertEqual(tax.to_dict()["COFINS"]["COFINSAliq"]["CST"], "01")

    def test_cofins_nt_wrapped_by_tag(self):
        tax = Tax(cofins=CofinsNt(cst="07"))
        self.assertEqual(tax.to_dict()["COFINS"], {"COFINSNT": {"CST": "07"}})

    def test_cofins_outr_wrapped_by_tag(self):
        tax = Tax(cofins=CofinsOutr(cst="99", v_cofins="0.00"))
        self.assertEqual(
            tax.to_dict()["COFINS"],
            {"COFINSOutr": {"CST": "99", "vCOFINS": "0.00"}},
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
            {"vTotTrib", "ICMS", "ICMSUFDest", "IPI", "PIS", "COFINS"},
        )


class TestWrapHelper(unittest.TestCase):
    def test_wrap_passes_raw_dict_through_unchanged(self):
        self.assertEqual(
            _wrap({"ICMS00": {"orig": "0"}}, {}), {"ICMS00": {"orig": "0"}}
        )

    def test_wrap_nests_model_under_its_tag(self):
        result = _wrap(
            IcmsSn102(orig="0", csosn="102"), {IcmsSn102: "ICMSSN102"}
        )
        self.assertEqual(result, {"ICMSSN102": {"orig": "0", "CSOSN": "102"}})


if __name__ == "__main__":
    unittest.main()
