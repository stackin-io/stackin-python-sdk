import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from stackin import DocumentType, FiscalReference, Invoice
from tests.test_issue_options import BRAZIL, nfe_item
from tests.test_reference import FakeResponse

ROW = {
    "nbs": "115021000",
    "description": "Servicos",
    "operation_indicator": "010101",
    "ibs_cbs_classification": "200034",
    "classification_name": "Reducao",
    "classification_cst": "200",
    "reduction_ibs": 60.0,
    "reduction_cbs": None,
    "legal_reference": "Art. 129 da LC 214/2025",
    "incidence": "Local do fornecedor",
    "operation_variants": {
        "onerous_domestic": "010101",
        "onerous_abroad": "010201",
        "free_domestic": "010301",
        "free_abroad": "010401",
    },
}


def _invoice():
    return Invoice(base_url="https://sdk.test", api_key="k")


def _call(call, payload=None):
    with patch("stackin.core.client.requests.request") as request:
        request.return_value = FakeResponse(200, payload)
        call()
    return request.call_args


def _issue(client, **extra):
    return client.issue(
        document_type=DocumentType.NFE,
        client_name="Buyer",
        tax_id="12345678909",
        items=[nfe_item()],
        recipient_address=BRAZIL,
        contingency=True,
        **extra,
    )


class NbsSuggestionFieldsTest(unittest.TestCase):
    def test_new_fields_are_read(self):
        payload = {
            "service_code": "010701",
            "suggestions": [ROW],
            "source": {"path": "x", "date": None},
        }
        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(200, payload)
            result = FiscalReference(
                base_url="https://sdk.test", api_key="k"
            ).nbs_suggestions("1.07")
        found = result.suggestions[0]
        self.assertEqual(found.classification_cst, "200")
        self.assertEqual(found.reduction_ibs, 60.0)
        self.assertIsNone(found.reduction_cbs)
        self.assertEqual(found.legal_reference, "Art. 129 da LC 214/2025")
        self.assertEqual(found.incidence, "Local do fornecedor")
        self.assertEqual(found.operation_variants, ROW["operation_variants"])

    def test_older_rows_leave_them_empty(self):
        payload = {
            "service_code": "010701",
            "suggestions": [{"nbs": "115021000"}],
            "source": {"path": "x"},
        }
        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(200, payload)
            result = FiscalReference(
                base_url="https://sdk.test", api_key="k"
            ).nbs_suggestions("1.07")
        found = result.suggestions[0]
        self.assertIsNone(found.classification_cst)
        self.assertIsNone(found.operation_variants)


class ContingencyTest(unittest.TestCase):
    def test_started_at_and_reason_reach_the_body(self):
        started = datetime(2026, 11, 25, 9, 0, tzinfo=timezone(timedelta(hours=-3)))
        call = _call(
            lambda: _issue(
                _invoice(),
                contingency_started_at=started,
                contingency_reason="SEFAZ authorizer unavailable",
            )
        )
        body = call.kwargs["json"]
        self.assertTrue(body["contingency"])
        self.assertEqual(body["contingency_started_at"], "2026-11-25T09:00:00-03:00")
        self.assertEqual(body["contingency_reason"], "SEFAZ authorizer unavailable")

    def test_left_out_when_unset(self):
        body = _call(lambda: _issue(_invoice())).kwargs["json"]
        self.assertNotIn("contingency_started_at", body)
        self.assertNotIn("contingency_reason", body)

    def test_naive_started_at_is_refused(self):
        with self.assertRaises(ValueError):
            _issue(_invoice(), contingency_started_at=datetime(2026, 11, 25, 9, 0))

    def test_validate_takes_them_too(self):
        call = _call(
            lambda: _invoice().validate(
                document_type=DocumentType.NFE,
                client_name="Buyer",
                tax_id="12345678909",
                items=[nfe_item()],
                recipient_address=BRAZIL,
                contingency=True,
                contingency_reason="SEFAZ authorizer unavailable",
            ),
            {"valid": True, "errors": [], "warnings": []},
        )
        self.assertEqual(
            call.kwargs["json"]["contingency_reason"], "SEFAZ authorizer unavailable"
        )


class AcceptLanguageTest(unittest.TestCase):
    def test_classify_sends_the_header_and_origin_answer(self):
        call = _call(
            lambda: _invoice().classify(
                "Camiseta de algodao",
                document_type=DocumentType.NFE,
                answers={"origin": "resale"},
                accept_language="en",
            )
        )
        self.assertEqual(call.kwargs["headers"]["Accept-Language"], "en")
        self.assertEqual(call.kwargs["json"]["answers"], {"origin": "resale"})
        self.assertNotIn("accept_language", call.kwargs["json"])

    def test_received_sends_the_header(self):
        call = _call(
            lambda: _invoice().received(limit=5, accept_language="es"),
            {"data": []},
        )
        self.assertEqual(call.kwargs["headers"]["Accept-Language"], "es")

    def test_no_header_when_unset(self):
        call = _call(lambda: _invoice().received(), {"data": []})
        self.assertNotIn("Accept-Language", call.kwargs["headers"])
