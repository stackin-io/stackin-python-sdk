import unittest
from decimal import Decimal

from pydantic import ValidationError

from stackin.br import (
    CofinsNt,
    IbsCbs,
    IcmsSn102,
    PisNt,
    PresumedCredit,
    Product,
    Tax,
)


class TestProductToDict(unittest.TestCase):
    def test_minimal_product(self):
        product = Product(description="Servico basico", amount=100.0)
        data = product.to_dict()

        self.assertEqual(data["description"], "Servico basico")
        self.assertEqual(data["amount"], "100.0")
        self.assertEqual(
            data["product"],
            {"unit": "UN", "quantity": 1.0, "used_movable_asset": False},
        )
        self.assertIsNone(data["service_code"])
        self.assertIsNone(data["discount"])
        self.assertFalse(data["tax_retained"])
        self.assertIsNone(data["observations"])

    def test_br_fields_nest_under_br(self):
        product = Product(
            description="Produto",
            amount=50.0,
            ncm="84713012",
            cfop="5102",
            cest="0300700",
        )
        data = product.to_dict()

        self.assertEqual(data["product"]["br"]["ncm"], "84713012")
        self.assertEqual(data["product"]["br"]["cfop"], "5102")
        self.assertEqual(data["product"]["br"]["cest"], "0300700")

    def test_presumed_credits(self):
        product = Product(
            description="Produto",
            amount=50.0,
            ncm="84713012",
            cfop="5102",
            presumed_credits=[
                PresumedCredit(code="PR820001", percentage=3.0, amount=2.40)
            ],
        )
        data = product.to_dict()

        self.assertEqual(
            data["product"]["br"]["presumed_credits"],
            [{"code": "PR820001", "percentage": 3.0, "amount": 2.40}],
        )

    def test_extra_groups_merged_into_br(self):
        product = Product(
            description="Produto",
            amount=50.0,
            ncm="84713012",
            cfop="5102",
            extra_groups={"custom_field": "value"},
        )
        data = product.to_dict()

        self.assertEqual(
            data["product"]["br"]["extra_groups"], {"custom_field": "value"}
        )

    def test_typed_tax_serializes_via_tax_to_dict(self):
        product = Product(
            description="Produto",
            amount=50.0,
            ncm="84713012",
            cfop="5102",
            tax=Tax(
                icms=IcmsSn102(orig="0", csosn="102"),
                pis=PisNt(cst="07"),
                cofins=CofinsNt(cst="07"),
            ),
        )
        data = product.to_dict()

        self.assertEqual(
            data["product"]["br"]["tax"],
            {
                "icms": {"orig": "0", "csosn": "102"},
                "pis": {"cst": "07"},
                "cofins": {"cst": "07"},
            },
        )

    def test_nfse_fields(self):
        product = Product(
            description="Consultoria",
            amount=1500.0,
            service_code="1.06",
            service_discount=50.0,
            tax_retained=True,
            observations="Nota de teste",
        )
        data = product.to_dict()

        self.assertEqual(data["service_code"], "1.06")
        self.assertEqual(data["discount"], 50.0)
        self.assertTrue(data["tax_retained"])
        self.assertEqual(data["observations"], "Nota de teste")
        self.assertNotIn("br", data["product"])

    def test_raw_dict_tax_assigned_after_construction_is_passed_through(self):
        product = Product(
            description="Produto", amount=50.0, ncm="84713012", cfop="5102"
        )
        product.tax = {"ICMS": {"ICMS00": {"orig": "0"}}}
        data = product.to_dict()

        self.assertEqual(
            data["product"]["br"]["tax"], {"ICMS": {"ICMS00": {"orig": "0"}}}
        )

    def test_quantity_and_extra_expenses(self):
        product = Product(
            description="Produto",
            amount=10.0,
            unit="CX",
            quantity=20,
            barcode="7891000100103",
            freight=15.0,
            insurance=5.0,
            discount=10.0,
            other_expenses=3.5,
            used_movable_asset=True,
            purchase_order="PC-1",
            purchase_order_item="1",
        )
        data = product.to_dict()

        product_data = data["product"]
        self.assertEqual(product_data["unit"], "CX")
        self.assertEqual(product_data["quantity"], 20)
        self.assertEqual(product_data["barcode"], "7891000100103")
        self.assertEqual(product_data["freight"], 15.0)
        self.assertEqual(product_data["insurance"], 5.0)
        self.assertEqual(product_data["discount"], 10.0)
        self.assertEqual(product_data["other_expenses"], 3.5)
        self.assertTrue(product_data["used_movable_asset"])
        self.assertEqual(product_data["purchase_order"], "PC-1")
        self.assertEqual(product_data["purchase_order_item"], "1")


if __name__ == "__main__":
    unittest.main()


class TestUnitPrice(unittest.TestCase):
    """`unit_price` is one unit; `amount` is the line's gross total."""

    def test_a_line_priced_per_unit(self):
        product = Product(
            description="Teclado",
            quantity=Decimal("2"),
            unit_price=Decimal("120.00"),
            unit="UN",
            ncm="84716052",
            cfop="5102",
        )

        data = product.to_dict()

        self.assertEqual(data["unit_price"], "120.00")
        self.assertIsNone(data["amount"])
        self.assertEqual(data["product"]["quantity"], 2.0)

    def test_the_legacy_line_still_sends_only_a_total(self):
        product = Product(description="Servico", amount=Decimal("100.00"))

        data = product.to_dict()

        self.assertEqual(data["amount"], "100.00")
        self.assertIsNone(data["unit_price"])

    def test_both_may_be_sent_when_they_agree(self):
        product = Product(
            description="Teclado",
            quantity=Decimal("2"),
            unit_price=Decimal("120.00"),
            amount=Decimal("240.00"),
        )

        data = product.to_dict()

        self.assertEqual(data["unit_price"], "120.00")
        self.assertEqual(data["amount"], "240.00")

    def test_the_tenth_place_survives_the_wire(self):
        """A float would round it away before the request is built."""
        product = Product(
            description="Granel",
            quantity=Decimal("1"),
            unit_price=Decimal("0.0000000001"),
        )

        self.assertEqual(product.to_dict()["unit_price"], "0.0000000001")

    def test_a_line_may_carry_neither(self):
        """The API decides, so the SDK does not refuse a payload twice."""
        product = Product(description="Servico")

        data = product.to_dict()

        self.assertIsNone(data["amount"])
        self.assertIsNone(data["unit_price"])

    def test_a_unit_price_of_zero_is_refused_here(self):
        with self.assertRaises(ValidationError):
            Product(description="Servico", unit_price=Decimal("0"))


class TestIbsCbs(unittest.TestCase):
    """The Reforma Tributária group, required from 2026 for regime normal."""

    def group(self, **overrides) -> dict:
        values = {
            "cst": "000",
            "classification": "000001",
            "rate_state": 0.1,
            "rate_city": 0.0,
            "rate_federal": 0.9,
        }
        values.update(overrides)
        return values

    def test_it_nests_under_br_like_every_other_fiscal_field(self):
        product = Product(
            description="Teclado",
            unit_price=Decimal("120.00"),
            ncm="84716052",
            cfop="5102",
            ibs_cbs=IbsCbs(**self.group()),
        )

        data = product.to_dict()

        self.assertEqual(data["product"]["br"]["ibs_cbs"]["cst"], "000")

    def test_an_item_without_it_sends_nothing(self):
        """This is what an NF-e looked like before the reform."""
        product = Product(description="Teclado", unit_price=Decimal("10.00"))

        self.assertNotIn("br", product.to_dict()["product"])

    def test_the_base_is_optional_and_defaults_to_the_item_amount(self):
        group = IbsCbs(**self.group())

        self.assertIsNone(group.base)

    def test_a_cst_that_is_not_three_digits_is_refused(self):
        with self.assertRaises(ValidationError):
            IbsCbs(**self.group(cst="00"))

    def test_a_classification_that_is_not_six_digits_is_refused(self):
        with self.assertRaises(ValidationError):
            IbsCbs(**self.group(classification="0001"))

    def test_a_negative_rate_is_refused(self):
        with self.assertRaises(ValidationError):
            IbsCbs(**self.group(rate_state=-1))

    def test_a_zero_rate_is_allowed(self):
        """A municipality with no IBS rate is a real case, not an error."""
        self.assertEqual(IbsCbs(**self.group(rate_city=0)).rate_city, 0)
