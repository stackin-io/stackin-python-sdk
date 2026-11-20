import json
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from unittest.mock import patch

from pydantic import ValidationError

from stackin import Address, Direction, DocumentType, Invoice, Purpose
from stackin.br import Export, Fuel, Product

KEY = "35261112345678000195550010000000011000000014"

BRAZIL = Address(
    street="Avenida Atlantica",
    number="500",
    neighborhood="Copacabana",
    city="Rio de Janeiro",
    state="RJ",
    zip_code="22010000",
)

ABROAD = Address(
    street="Fifth Avenue",
    number="700",
    neighborhood="Midtown",
    city="New York",
    state="EX",
    country_code="2496",
    country_name="Estados Unidos",
)


def nfe_item(**fields):
    return Product(
        description="Teclado", amount=Decimal("10.00"), ncm="84716052", cfop="5102"
    ).model_copy(update=fields)


class IssueCase(unittest.TestCase):
    def setUp(self):
        self.client = Invoice(api_key="test-key")

    def body(self, **fields):
        """The JSON the API would receive for one issue() call."""
        call: dict[str, Any] = {
            "document_type": DocumentType.NFE,
            "client_name": "Buyer",
            "tax_id": "11111111111111",
            "items": [nfe_item()],
            "recipient_address": BRAZIL,
        }
        call.update(fields)
        with patch.object(self.client, "_request", return_value={}) as sent:
            self.client.issue(**call)
        return sent.call_args.kwargs["json"]


class TestUnsetFieldsLeaveTheBodyAlone(IssueCase):
    def test_an_existing_call_sends_exactly_what_it_sent_before(self):
        self.assertEqual(
            json.dumps(self.body()),
            json.dumps(
                {
                    "document_type": "nfe",
                    "client_name": "Buyer",
                    "tax_id": "11111111111111",
                    "items": [nfe_item().to_dict()],
                    "recipient_address": {
                        "state": "RJ",
                        "street": "Avenida Atlantica",
                        "number": "500",
                        "neighborhood": "Copacabana",
                        "city": "Rio de Janeiro",
                        "zip_code": "22010000",
                    },
                }
            ),
        )

    def test_no_new_key_appears_when_unset(self):
        body = self.body()
        for key in (
            "discount",
            "issued_at",
            "purpose",
            "direction",
            "referenced_keys",
            "foreign_id",
            "export",
            "contingency",
        ):
            with self.subTest(key=key):
                self.assertNotIn(key, body)
        self.assertNotIn("fuel", body["items"][0]["product"].get("br", {}))


class TestContingency(IssueCase):
    def test_true_is_sent(self):
        self.assertIs(self.body(contingency=True)["contingency"], True)

    def test_false_is_left_out(self):
        self.assertNotIn("contingency", self.body(contingency=False))


class TestDiscount(IssueCase):
    def test_sent_as_a_decimal_string(self):
        self.assertEqual(self.body(discount=Decimal("12.50"))["discount"], "12.50")

    def test_zero_is_sent(self):
        self.assertEqual(self.body(discount=Decimal("0"))["discount"], "0")

    def test_a_negative_discount_is_refused(self):
        with self.assertRaisesRegex(ValueError, "discount must be zero or more"):
            self.body(discount=Decimal("-1"))

    def test_not_a_number_is_refused(self):
        for value in (Decimal("NaN"), "ten"):
            with (
                self.subTest(value=value),
                self.assertRaisesRegex(ValueError, "discount must be"),
            ):
                self.body(discount=value)


class TestIssuedAt(IssueCase):
    def test_sent_as_iso_8601_with_its_offset(self):
        moment = datetime(2026, 11, 15, 10, 30, tzinfo=timezone(timedelta(hours=-3)))

        self.assertEqual(
            self.body(issued_at=moment)["issued_at"], "2026-11-15T10:30:00-03:00"
        )

    def test_a_naive_datetime_is_refused(self):
        with self.assertRaisesRegex(ValueError, "issued_at must be timezone-aware"):
            self.body(issued_at=datetime(2026, 11, 15, 10, 30))

    def test_a_string_is_refused(self):
        with self.assertRaisesRegex(ValueError, "issued_at must be a datetime"):
            self.body(issued_at="2026-11-15T10:30:00-03:00")


class TestPurposeAndDirection(IssueCase):
    def test_sent_as_their_wire_values(self):
        body = self.body(
            purpose=Purpose.RETURN,
            direction=Direction.IN,
            referenced_keys=[KEY],
        )

        self.assertEqual(body["purpose"], "return")
        self.assertEqual(body["direction"], "in")
        self.assertEqual(body["referenced_keys"], [KEY])

    def test_every_purpose_is_accepted(self):
        for purpose in Purpose:
            with self.subTest(purpose=purpose):
                self.assertEqual(self.body(purpose=purpose)["purpose"], purpose.value)

    def test_an_unknown_value_is_refused(self):
        with self.assertRaises(ValueError):
            self.body(purpose="devolucao")
        with self.assertRaises(ValueError):
            self.body(direction="sideways")

    def test_a_bare_string_of_keys_is_refused(self):
        with self.assertRaisesRegex(
            ValueError, "referenced_keys must be a list of access keys"
        ):
            self.body(referenced_keys=KEY)


class TestBuyerAbroad(IssueCase):
    def test_tax_id_may_be_left_out_on_an_nfe_abroad(self):
        body = self.body(
            tax_id=None,
            recipient_address=ABROAD,
            foreign_id="P1234567",
            export=Export(exit_state="SP", place="Porto de Santos"),
        )

        self.assertNotIn("tax_id", body)
        self.assertEqual(body["foreign_id"], "P1234567")
        self.assertEqual(
            body["export"], {"exit_state": "SP", "place": "Porto de Santos"}
        )
        self.assertEqual(
            body["recipient_address"],
            {
                "state": "EX",
                "street": "Fifth Avenue",
                "number": "700",
                "neighborhood": "Midtown",
                "city": "New York",
                "country_code": "2496",
                "country_name": "Estados Unidos",
            },
        )

    def test_dispatch_place_is_sent_when_given(self):
        export = Export(exit_state="SP", place="Santos", dispatch_place="Alfandega")

        self.assertEqual(
            self.body(tax_id=None, recipient_address=ABROAD, export=export)["export"],
            {"exit_state": "SP", "place": "Santos", "dispatch_place": "Alfandega"},
        )

    def test_tax_id_stays_required_in_brazil(self):
        with self.assertRaisesRegex(ValueError, "tax_id is required"):
            self.body(tax_id=None)

    def test_tax_id_stays_required_on_an_nfse(self):
        with self.assertRaisesRegex(ValueError, "tax_id is required"):
            self.body(
                document_type=DocumentType.NFSE,
                tax_id=None,
                items=[Product(description="Servico", amount=Decimal("10"))],
                recipient_address=None,
            )

    def test_zip_code_may_be_left_out_abroad(self):
        self.assertNotIn(
            "zip_code",
            self.body(tax_id=None, recipient_address=ABROAD)["recipient_address"],
        )

    def test_zip_code_stays_required_in_brazil(self):
        address = BRAZIL.model_copy(update={"zip_code": None})

        with self.assertRaisesRegex(
            ValueError, "missing required fields for NFE: zip_code"
        ):
            self.body(recipient_address=address)

    def test_the_country_is_required_abroad(self):
        address = ABROAD.model_copy(update={"country_code": None})

        with self.assertRaisesRegex(
            ValueError, "missing required fields for NFE: country_code"
        ):
            self.body(tax_id=None, recipient_address=address)

    def test_the_bacen_check_digit_is_not_checked(self):
        address = ABROAD.model_copy(update={"country_code": "9999"})

        body = self.body(tax_id=None, recipient_address=address)

        self.assertEqual(body["recipient_address"]["country_code"], "9999")

    def test_export_fields_are_latin1_checked(self):
        with self.assertRaisesRegex(ValueError, "export.place contains a character"):
            self.body(
                tax_id=None,
                recipient_address=ABROAD,
                export=Export(exit_state="SP", place="Port 上海"),
            )


class TestLatin1CheckSkipsWhatNeverReachesTheXml(IssueCase):
    def test_new_metadata_fields_are_not_walked(self):
        walked: list[dict] = []
        with patch(
            "stackin.core.client._validate_nfe_latin1",
            side_effect=lambda payload: walked.append(json.loads(json.dumps(payload))),
        ):
            self.body(
                discount=Decimal("1"),
                issued_at=datetime(2026, 11, 15, tzinfo=timezone.utc),
                purpose=Purpose.NORMAL,
                direction=Direction.OUT,
                referenced_keys=[KEY],
                foreign_id="P1234567",
                external_reference="order-1",
            )

        for key in (
            "discount",
            "issued_at",
            "purpose",
            "direction",
            "referenced_keys",
            "foreign_id",
            "external_reference",
        ):
            with self.subTest(key=key):
                self.assertNotIn(key, walked[0])

    def test_a_non_latin1_key_is_left_to_the_api(self):
        body = self.body(referenced_keys=["\u2713" * 44])

        self.assertEqual(body["referenced_keys"], ["\u2713" * 44])


class TestExport(unittest.TestCase):
    def test_exit_state_and_place_are_required(self):
        with self.assertRaises(ValidationError):
            Export.model_validate({"place": "Santos"})
        with self.assertRaises(ValidationError):
            Export.model_validate({"exit_state": "SP"})

    def test_place_is_at_most_60_characters(self):
        with self.assertRaises(ValidationError):
            Export(exit_state="SP", place="x" * 61)


class TestFuelOnTheWire(IssueCase):
    def test_sent_under_the_product_br_fuel_key(self):
        fuel = Fuel(
            anp_code="320102001",
            anp_description="GASOLINA C COMUM",
            consumer_state="SP",
        )

        body = self.body(items=[nfe_item(fuel=fuel)])

        self.assertEqual(
            body["items"][0]["product"]["br"]["fuel"],
            {
                "anp_code": "320102001",
                "anp_description": "GASOLINA C COMUM",
                "consumer_state": "SP",
            },
        )


if __name__ == "__main__":
    unittest.main()
