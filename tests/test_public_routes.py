"""Stats, readiness, rejection, classification, invalidations and cities."""

import unittest
from unittest.mock import patch

from stackin import DocumentType, FiscalReference, Invoice
from tests.test_reference import FakeResponse

BASE = "https://sdk.test/api/v1"
INVOICE_ID = "9f0e1d2c-3b4a-5968-7766-554433221100"


def _invoice():
    return Invoice(base_url="https://sdk.test", api_key="k")


def _sent(call, client, payload=None):
    with patch("stackin.core.client.requests.request") as request:
        request.return_value = FakeResponse(200, payload if payload is not None else {})
        result = call(client)
    return request.call_args, result


class StatsTest(unittest.TestCase):
    def test_no_days_sends_no_params(self):
        (args, kwargs), _ = _sent(lambda c: c.stats(), _invoice())

        self.assertEqual(args[:2], ("GET", f"{BASE}/invoices/stats"))
        self.assertEqual(kwargs["params"], {})

    def test_days_goes_out(self):
        (_, kwargs), result = _sent(
            lambda c: c.stats(days=7),
            _invoice(),
            {"total": 3, "period_days": 7},
        )

        self.assertEqual(kwargs["params"], {"days": 7})
        self.assertEqual(result["total"], 3)

    def test_days_outside_the_api_bounds_is_refused(self):
        for days in (0, 366):
            with (
                self.subTest(days=days),
                self.assertRaisesRegex(ValueError, "days"),
            ):
                _invoice().stats(days=days)

    def test_company_names_the_header(self):
        (_, kwargs), _ = _sent(lambda c: c.stats(company="acme"), _invoice())

        self.assertEqual(kwargs["headers"]["X-Stackin-Company"], "acme")


class ReadinessTest(unittest.TestCase):
    def test_reads_the_company(self):
        payload = {"ready": False, "missing": ["certificate"]}
        (args, kwargs), result = _sent(lambda c: c.readiness(), _invoice(), payload)

        self.assertEqual(args[:2], ("GET", f"{BASE}/company"))
        self.assertIsNone(kwargs["json"])
        self.assertEqual(result, payload)


class RejectionTest(unittest.TestCase):
    def test_reads_by_invoice_id(self):
        payload = {"code": "539", "steps": ["Use the next number"]}
        (args, _), result = _sent(
            lambda c: c.rejection(INVOICE_ID), _invoice(), payload
        )

        self.assertEqual(args[:2], ("GET", f"{BASE}/invoices/{INVOICE_ID}/rejection"))
        self.assertEqual(result["code"], "539")


class ClassifyTest(unittest.TestCase):
    def test_minimal_body(self):
        (args, kwargs), _ = _sent(
            lambda c: c.classify("Teclado USB", document_type=DocumentType.NFE),
            _invoice(),
        )

        self.assertEqual(args[:2], ("POST", f"{BASE}/ai/classify"))
        self.assertEqual(
            kwargs["json"],
            {"description": "Teclado USB", "document_type": "nfe"},
        )

    def test_state_and_answers_go_out(self):
        (_, kwargs), _ = _sent(
            lambda c: c.classify(
                "Cerveja artesanal",
                document_type=DocumentType.NFE,
                recipient_state="sp",
                answers={
                    "operation_scope": "interstate",
                    "contains_alcohol": True,
                },
            ),
            _invoice(),
        )

        self.assertEqual(kwargs["json"]["recipient_state"], "SP")
        self.assertEqual(
            kwargs["json"]["answers"],
            {"operation_scope": "interstate", "contains_alcohol": True},
        )

    def test_description_bounds(self):
        for description in ("ab", "x" * 501):
            with (
                self.subTest(size=len(description)),
                self.assertRaisesRegex(ValueError, "description"),
            ):
                _invoice().classify(description, document_type=DocumentType.NFSE)

    def test_state_must_be_a_uf(self):
        with self.assertRaisesRegex(ValueError, "recipient_state"):
            _invoice().classify(
                "Teclado",
                document_type=DocumentType.NFE,
                recipient_state="SAO",
            )


class InvalidationsTest(unittest.TestCase):
    def test_no_filter_sends_no_params(self):
        (args, kwargs), _ = _sent(lambda c: c.invalidations(), _invoice())

        self.assertEqual(args[:2], ("GET", f"{BASE}/invoices/invalidations"))
        self.assertEqual(kwargs["params"], {})

    def test_pagination_goes_out(self):
        (_, kwargs), _ = _sent(
            lambda c: c.invalidations(
                limit=10, offset=20, sort_by="created_at", order_by="asc"
            ),
            _invoice(),
        )

        self.assertEqual(
            kwargs["params"],
            {
                "limit": 10,
                "offset": 20,
                "sort_by": "created_at",
                "order_by": "asc",
            },
        )


class CitiesTest(unittest.TestCase):
    def _ref(self):
        return FiscalReference(base_url="https://sdk.test", api_key="k")

    def test_name_and_default_country(self):
        rows = [
            {
                "country": "BR",
                "code": "3550308",
                "name": "São Paulo",
                "state": "SP",
            }
        ]
        (args, kwargs), result = _sent(lambda c: c.cities("sao"), self._ref(), rows)

        self.assertEqual(args[:2], ("GET", f"{BASE}/cities"))
        self.assertEqual(kwargs["params"], {"name": "sao", "country": "BR"})
        self.assertEqual(result, rows)

    def test_state_is_upper_cased(self):
        (_, kwargs), _ = _sent(
            lambda c: c.cities("campinas", state="sp"), self._ref(), []
        )

        self.assertEqual(kwargs["params"]["state"], "SP")

    def test_name_bounds(self):
        with self.assertRaisesRegex(ValueError, "name"):
            self._ref().cities("a")

    def test_state_must_be_two_letters(self):
        with self.assertRaisesRegex(ValueError, "state"):
            self._ref().cities("campinas", state="SPX")
