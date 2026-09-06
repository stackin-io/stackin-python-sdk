import unittest

from stackin.br import CofinsNt, IcmsSn102, PisNt, PresumedCredit, Product, Tax


class TestProductToDict(unittest.TestCase):
    def test_minimal_product(self):
        product = Product(description="Servico basico", amount=100.0)
        data = product.to_dict()

        self.assertEqual(data["description"], "Servico basico")
        self.assertEqual(data["amount"], 100.0)
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
