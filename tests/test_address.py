import unittest

from pydantic import ValidationError

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


class TestAddressMinimumLength(unittest.TestCase):
    """xLgr and xBairro take at least 2 characters in the NF-e XSD."""

    def test_two_characters_are_enough(self):
        address = Address(street="Av", neighborhood="Bo")

        self.assertEqual(address.street, "Av")
        self.assertEqual(address.neighborhood, "Bo")

    def test_a_one_character_field_is_refused(self):
        for field in ("street", "neighborhood"):
            with (
                self.subTest(field=field),
                self.assertRaisesRegex(
                    ValidationError, f"{field} must have at least 2 characters"
                ),
            ):
                Address(**{field: "A"})

    def test_padding_does_not_count(self):
        with self.assertRaisesRegex(
            ValidationError, "street must have at least 2 characters"
        ):
            Address(street="  A  ")

    def test_absent_fields_are_not_checked(self):
        self.assertEqual(Address(state="SP").to_dict(), {"state": "SP"})


class TestAddressAbroad(unittest.TestCase):
    def test_country_fields_are_sent_when_set(self):
        address = Address(state="EX", country_code="0639", country_name="Argentina")

        self.assertEqual(
            address.to_dict(),
            {"state": "EX", "country_code": "0639", "country_name": "Argentina"},
        )

    def test_country_code_takes_one_to_four_digits(self):
        for code in ("", "12345", "US"):
            with self.subTest(code=code), self.assertRaises(ValidationError):
                Address(country_code=code)

    def test_the_bacen_check_digit_is_not_checked(self):
        self.assertEqual(Address(country_code="9999").country_code, "9999")


if __name__ == "__main__":
    unittest.main()
