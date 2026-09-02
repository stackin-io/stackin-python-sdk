import unittest

from stackin import Address


class TestAddressToDict(unittest.TestCase):
    def test_empty_address(self):
        self.assertEqual(Address().to_dict(), {})

    def test_full_address(self):
        address = Address(
            street="Rua das Flores",
            number="123",
            neighborhood="Centro",
            city="Sao Paulo",
            state="SP",
            zip_code="01310100",
            city_code="3550308",
        )
        self.assertEqual(
            address.to_dict(),
            {
                "street": "Rua das Flores",
                "number": "123",
                "neighborhood": "Centro",
                "city": "Sao Paulo",
                "state": "SP",
                "zip_code": "01310100",
                "city_code": "3550308",
            },
        )

    def test_partial_address_omits_none_fields(self):
        address = Address(state="SC")
        self.assertEqual(address.to_dict(), {"state": "SC"})


if __name__ == "__main__":
    unittest.main()
