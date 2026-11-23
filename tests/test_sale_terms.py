import json
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from unittest.mock import patch

from pydantic import ValidationError

from stackin import DocumentType, Invoice
from stackin.br import (
    Intermediary,
    Payment,
    PaymentCard,
    Product,
    SaleTerms,
    Transport,
    TransportVolume,
)
from tests.test_issue_options import BRAZIL, nfe_item
from tests.test_reference import FakeResponse

CNPJ = "11222333000181"


class IssueCase(unittest.TestCase):
    def setUp(self):
        self.client = Invoice(api_key="test-key")

    def body(self, **fields):
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


TERM_KEYS = {"presence", "intermediary", "transport", "payments", "change"}


class TestBodySerialization(IssueCase):
    def test_unset_terms_are_not_in_the_body(self):
        body = self.body()

        self.assertFalse(TERM_KEYS & set(body))
        self.assertNotIn("net_weight", body["items"][0]["product"])
        self.assertNotIn("gross_weight", body["items"][0]["product"])

    def test_every_term_goes_out_by_its_api_name(self):
        body = self.body(
            presence="2",
            intermediary=Intermediary(tax_id=CNPJ, identifier="loja-42"),
            transport=Transport(
                freight_mode="1",
                volumes=[
                    TransportVolume(
                        quantity=2,
                        species="CAIXA",
                        brand="ACME",
                        numbering="1/2",
                        net_weight=Decimal("1.5"),
                        gross_weight=Decimal("1.75"),
                    )
                ],
            ),
            payments=[
                Payment(
                    method="03",
                    amount=Decimal("10"),
                    card=PaymentCard(
                        integration="1",
                        tax_id=CNPJ,
                        brand="01",
                        authorization="ABC123",
                    ),
                ),
                Payment(method="99", amount=Decimal("5.50"), description="Vale"),
            ],
            change=Decimal("5.50"),
        )

        self.assertEqual(body["presence"], "2")
        self.assertEqual(
            body["intermediary"], {"tax_id": CNPJ, "identifier": "loja-42"}
        )
        self.assertEqual(
            body["transport"],
            {
                "freight_mode": "1",
                "volumes": [
                    {
                        "quantity": 2,
                        "species": "CAIXA",
                        "brand": "ACME",
                        "numbering": "1/2",
                        "net_weight": "1.5",
                        "gross_weight": "1.75",
                    }
                ],
            },
        )
        self.assertEqual(
            body["payments"],
            [
                {
                    "method": "03",
                    "amount": "10",
                    "card": {
                        "integration": "1",
                        "tax_id": CNPJ,
                        "brand": "01",
                        "authorization": "ABC123",
                    },
                },
                {"method": "99", "amount": "5.50", "description": "Vale"},
            ],
        )
        self.assertEqual(body["change"], "5.50")
        json.dumps(body)

    def test_a_zero_change_is_sent(self):
        self.assertEqual(self.body(change=Decimal("0"))["change"], "0")

    def test_transport_without_volumes_sends_none(self):
        body = self.body(transport=Transport(freight_mode="9"))

        self.assertEqual(body["transport"], {"freight_mode": "9"})

    def test_empty_volumes_are_sent_to_write_none(self):
        body = self.body(transport=Transport(freight_mode="0", volumes=[]))

        self.assertEqual(body["transport"], {"freight_mode": "0", "volumes": []})

    def test_line_weights_go_in_the_product_as_strings(self):
        item = nfe_item(net_weight=Decimal("0.350"), gross_weight=Decimal("0.4"))

        product = self.body(items=[item])["items"][0]["product"]

        self.assertEqual(product["net_weight"], "0.350")
        self.assertEqual(product["gross_weight"], "0.4")

    def test_a_zero_line_weight_is_sent(self):
        item = nfe_item(net_weight=Decimal("0"))

        self.assertEqual(
            self.body(items=[item])["items"][0]["product"]["net_weight"], "0"
        )

    def test_the_idempotency_key_stays_out_of_the_body(self):
        with patch.object(self.client, "_request", return_value={}) as sent:
            self.client.issue(
                document_type=DocumentType.NFE,
                client_name="Buyer",
                tax_id="11111111111111",
                items=[nfe_item()],
                recipient_address=BRAZIL,
                presence="1",
                idempotency_key="idem-1",
            )

        self.assertEqual(sent.call_args.kwargs["idempotency_key"], "idem-1")
        self.assertNotIn("idempotency_key", sent.call_args.kwargs["json"])
        self.assertEqual(sent.call_args.kwargs["json"]["presence"], "1")

    def test_validate_sends_the_same_terms(self):
        with patch.object(
            self.client, "_request", return_value={"valid": True, "errors": []}
        ) as sent:
            self.client.validate(
                document_type=DocumentType.NFE,
                client_name="Buyer",
                tax_id="11111111111111",
                items=[nfe_item()],
                recipient_address=BRAZIL,
                presence="3",
                change=Decimal("1"),
            )

        body = sent.call_args.kwargs["json"]
        self.assertEqual((body["presence"], body["change"]), ("3", "1"))

    def test_free_text_is_checked_for_latin1(self):
        with self.assertRaisesRegex(ValueError, "latin1"):
            self.body(
                transport=Transport(
                    freight_mode="1",
                    volumes=[TransportVolume(species="箱")],
                )
            )

    def test_issued_at_and_terms_travel_together(self):
        body = self.body(
            issued_at=datetime(2026, 11, 23, 10, tzinfo=timezone.utc), presence="1"
        )

        self.assertEqual(body["presence"], "1")
        self.assertIn("issued_at", body)


class TestValidation(IssueCase):
    def test_presence_must_be_in_the_code_set(self):
        for bad in ("6", "7", "", "x"):
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, "presence"):
                self.body(presence=bad)

    def test_every_presence_in_the_set_is_accepted(self):
        for code in ("0", "1", "2", "3", "4", "5", "9"):
            self.assertEqual(self.body(presence=code)["presence"], code)

    def test_freight_mode_must_be_in_the_code_set(self):
        with self.assertRaises(ValidationError):
            Transport(freight_mode="5")

    def test_volume_weights_take_three_decimals(self):
        with self.assertRaises(ValidationError):
            TransportVolume(net_weight=Decimal("1.2345"))
        with self.assertRaises(ValidationError):
            TransportVolume(gross_weight=Decimal("1.2345"))

    def test_amount_and_change_take_two_decimals(self):
        with self.assertRaises(ValidationError):
            Payment(method="01", amount=Decimal("1.234"))
        with self.assertRaisesRegex(ValueError, "change"):
            self.body(change=Decimal("1.005"))

    def test_line_weights_have_no_decimal_limit(self):
        item = nfe_item(net_weight=Decimal("0.1234567"))

        product = self.body(items=[item])["items"][0]["product"]
        self.assertEqual(product["net_weight"], "0.1234567")

    def test_volume_weights_cannot_be_negative(self):
        with self.assertRaises(ValidationError):
            TransportVolume(gross_weight=Decimal("-1"))

    def test_method_99_needs_a_description(self):
        with self.assertRaisesRegex(ValidationError, "description"):
            Payment(method="99", amount=Decimal("1"))

    def test_payment_method_is_two_digits_not_a_table(self):
        self.assertEqual(Payment(method="06", amount=Decimal("1")).method, "06")
        for bad in ("6", "1x", "003", ""):
            with self.subTest(bad=bad), self.assertRaisesRegex(ValidationError, "tPag"):
                Payment(method=bad, amount=Decimal("1"))

    def test_negative_amount_and_change_are_refused(self):
        with self.assertRaises(ValidationError):
            Payment(method="01", amount=Decimal("-1"))
        with self.assertRaisesRegex(ValueError, "change"):
            self.body(change=Decimal("-1"))

    def test_card_integration_is_any_string(self):
        self.assertEqual(PaymentCard(integration="7").to_dict(), {"integration": "7"})

    def test_identifier_length(self):
        with self.assertRaises(ValidationError):
            Intermediary(tax_id=CNPJ, identifier="a")

    def test_payments_cannot_be_empty(self):
        with self.assertRaisesRegex(ValueError, "payments"):
            self.body(payments=[])

    def test_negative_line_weight_is_refused(self):
        with self.assertRaises(ValidationError):
            Product(description="x", amount=Decimal("1"), net_weight=Decimal("-1"))


DETAIL = {
    "id": "5c1f0e2a-3b7d-4a96-8e41-9d2c7b6a1f03",
    "status": "authorized",
    "recipient_address": {"state": "SP"},
    "client_email": None,
    "client_phone": None,
    "presence": "2",
    "intermediary": {"tax_id": CNPJ, "identifier": "loja-42"},
    "transport": {
        "freight_mode": "1",
        "volumes": [
            {
                "quantity": 2,
                "species": "CAIXA",
                "net_weight": "1.500",
                "gross_weight": "1.750",
            }
        ],
    },
    "payments": [
        {
            "method": "03",
            "amount": "10.00",
            "card": {"integration": "2", "brand": "01"},
        },
        {"method": "99", "amount": "5.50", "description": "Vale"},
    ],
    "change": "5.50",
}


class TestDetailResult(unittest.TestCase):
    def test_the_stored_terms_parse_from_the_detail(self):
        terms = SaleTerms.from_invoice(DETAIL)

        self.assertEqual(terms.presence, "2")
        assert terms.intermediary and terms.transport and terms.payments
        self.assertEqual(terms.intermediary.identifier, "loja-42")
        self.assertEqual(terms.transport.freight_mode, "1")
        assert terms.transport.volumes
        self.assertEqual(terms.transport.volumes[0].net_weight, Decimal("1.500"))
        self.assertEqual(terms.payments[0].amount, Decimal("10.00"))
        assert terms.payments[0].card
        self.assertEqual(terms.payments[0].card.brand, "01")
        self.assertEqual(terms.payments[1].description, "Vale")
        self.assertEqual(terms.change, Decimal("5.50"))

    def test_a_detail_without_terms_parses_to_none(self):
        terms = SaleTerms.from_invoice(
            {"id": "x", "presence": None, "payments": None, "change": None}
        )

        self.assertEqual(terms, SaleTerms())

    def test_consult_by_the_client_leaves_the_dict_untouched(self):
        client = Invoice(api_key="k")
        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(200, DETAIL)
            result = client.history()

        self.assertEqual(SaleTerms.from_invoice(result).presence, "2")
