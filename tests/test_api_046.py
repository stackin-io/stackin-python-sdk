import unittest
from unittest.mock import patch

from stackin import (
    EVENTS,
    APIError,
    DocumentType,
    Invoice,
    PaymentRequiredError,
    RateLimitedError,
    ValidationResult,
)
from stackin.br import Product
from stackin.core.exceptions import _api_error
from tests.test_reference import FakeResponse

KEY = "35260112345678000195550010000000011000000011"


def _invoice():
    return Invoice(base_url="https://sdk.test", api_key="k")


def _items():
    return [Product(description="Consulting", amount="100.00")]


def _issue_kwargs():
    return {
        "document_type": DocumentType.NFSE,
        "client_name": "Acme",
        "tax_id": "12345678000195",
        "items": _items(),
    }


class ErrorFieldsTest(unittest.TestCase):
    def test_structured_rule_error(self):
        detail = {
            "code": "NCM_INVALID",
            "field": "items[0].product.br.ncm",
            "message": "NCM does not exist",
            "sefaz_rejection": "778",
            "expected": "8 digits",
            "received": "1",
        }

        error = _api_error(422, detail, {"detail": detail})

        self.assertEqual(error.code, "NCM_INVALID")
        self.assertEqual(error.field, "items[0].product.br.ncm")
        self.assertEqual(error.sefaz_rejection, "778")
        self.assertEqual(error.expected, "8 digits")
        self.assertEqual(error.received, "1")
        self.assertIsNone(error.retryable)
        self.assertEqual(str(error), "[422] NCM does not exist")
        self.assertEqual(error.detail, detail)

    def test_authority_error_block(self):
        body = {
            "detail": "The authority did not answer.",
            "error": {
                "code": "OUTCOME_UNKNOWN",
                "source": "authority",
                "message": "m",
                "retryable": False,
                "document_id": "DPS123",
                "invoice_id": "i",
            },
        }

        error = _api_error(502, body["detail"], body)

        self.assertEqual(error.code, "OUTCOME_UNKNOWN")
        self.assertIs(error.retryable, False)
        self.assertEqual(error.document_id, "DPS123")
        self.assertIsNone(error.field)
        self.assertEqual(error.status_code, 502)
        self.assertEqual(str(error), "[502] The authority did not answer.")

    def test_authority_rejected_prefers_the_block_code(self):
        body = {
            "detail": "Rejected.",
            "code": "AUTHORITY_REJECTED",
            "error": {"code": "539", "retryable": True},
        }

        error = _api_error(422, body["detail"], body)

        self.assertEqual(error.code, "539")
        self.assertIs(error.retryable, True)

    def test_top_level_code_without_error_block(self):
        body = {"detail": "Rejected.", "code": "AUTHORITY_REJECTED"}

        self.assertEqual(
            _api_error(422, body["detail"], body).code, "AUTHORITY_REJECTED"
        )

    def test_detail_code_on_other_dicts(self):
        detail = {"code": "RECEIVED_XML_NOT_AVAILABLE", "message": "Summary only"}

        error = _api_error(409, detail, {"detail": detail})

        self.assertIs(type(error), APIError)
        self.assertEqual(error.code, "RECEIVED_XML_NOT_AVAILABLE")

    def test_payment_required_carries_the_code(self):
        detail = {"code": "RECEIVED_PAYMENT_REQUIRED", "message": "No credit"}

        error = _api_error(402, detail, {"detail": detail})

        self.assertIsInstance(error, PaymentRequiredError)
        self.assertEqual(error.code, "RECEIVED_PAYMENT_REQUIRED")

    def test_rate_limit_code_stays(self):
        body = {"detail": "Wait", "code": "DISTRIBUTION_COOLDOWN"}

        error = _api_error(429, "Wait", body, {})

        self.assertIsInstance(error, RateLimitedError)
        self.assertEqual(error.code, "DISTRIBUTION_COOLDOWN")

    def test_pydantic_list_leaves_everything_null(self):
        detail = [{"loc": ["body"], "msg": "bad"}]

        error = _api_error(422, detail, {"detail": detail})

        self.assertIsNone(error.code)
        self.assertIsNone(error.field)
        self.assertIsNone(error.retryable)
        self.assertIsNone(error.document_id)
        self.assertIsNone(error.sefaz_rejection)
        self.assertEqual(error.detail, detail)

    def test_plain_text_body(self):
        error = _api_error(500, "boom", None)

        self.assertIsNone(error.code)
        self.assertEqual(str(error), "[500] boom")


class ReceivedXmlTest(unittest.TestCase):
    def test_returns_raw_bytes_without_decoding(self):
        response = FakeResponse(200)
        response.content = b"<nfeProc>\xe7\xe3</nfeProc>"

        with patch("stackin.core.client.requests.request") as request:
            request.return_value = response
            result = _invoice().received_xml(KEY, company="C1")

        self.assertEqual(result, b"<nfeProc>\xe7\xe3</nfeProc>")
        args, kwargs = request.call_args
        self.assertEqual(args[0], "GET")
        self.assertTrue(args[1].endswith(f"/api/v1/received-invoices/{KEY}/xml"))
        self.assertEqual(kwargs["headers"]["X-Stackin-Company"], "C1")

    def test_409_not_available_has_a_code(self):
        detail = {
            "code": "RECEIVED_XML_NOT_AVAILABLE",
            "message": "Summary only",
            "manifestation": {"method": "POST", "path": "/x"},
        }

        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(409, {"detail": detail})
            with self.assertRaises(APIError) as caught:
                _invoice().received_xml(KEY)

        self.assertEqual(caught.exception.status_code, 409)
        self.assertEqual(caught.exception.code, "RECEIVED_XML_NOT_AVAILABLE")

    def test_402_is_payment_required(self):
        detail = {"code": "RECEIVED_PAYMENT_REQUIRED", "message": "No credit"}

        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(402, {"detail": detail})
            with self.assertRaises(PaymentRequiredError) as caught:
                _invoice().received_xml(KEY)

        self.assertEqual(caught.exception.code, "RECEIVED_PAYMENT_REQUIRED")

    def test_access_key_is_one_segment(self):
        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(200)
            _invoice().received_xml("a/b")

        self.assertTrue(
            request.call_args[0][1].endswith("/received-invoices/a%2Fb/xml")
        )
        with self.assertRaises(ValueError):
            _invoice().received_xml("..")


class ConsultByDpsTest(unittest.TestCase):
    def test_gets_the_dps_path_and_unwraps_result(self):
        result = {"status": "cancelled", "access_key": KEY}

        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(200, {"result": result})
            got = _invoice().consult_by_dps("DPS123", company="C1")

        self.assertEqual(got, result)
        args, kwargs = request.call_args
        self.assertEqual(args[0], "GET")
        self.assertTrue(args[1].endswith("/api/v1/invoices/dps/DPS123"))
        self.assertEqual(kwargs["headers"]["X-Stackin-Company"], "C1")

    def test_dps_id_is_escaped_and_dots_refused(self):
        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(200, {"result": {}})
            _invoice().consult_by_dps("a/b?c")
            self.assertTrue(request.call_args[0][1].endswith("/dps/a%2Fb%3Fc"))
            with self.assertRaises(ValueError):
                _invoice().consult_by_dps("..")

    def test_404_raises(self):
        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(404, {"detail": "none"})
            with self.assertRaises(APIError) as caught:
                _invoice().consult_by_dps("DPS123")

        self.assertEqual(caught.exception.status_code, 404)


class ValidateTest(unittest.TestCase):
    def test_valid_with_warnings(self):
        body = {"valid": True, "warnings": [{"code": "W1", "message": "careful"}]}

        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(200, body)
            result = _invoice().validate(**_issue_kwargs(), company="C1")

        self.assertIsInstance(result, ValidationResult)
        self.assertTrue(result.valid)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.warnings[0].code, "W1")
        args, kwargs = request.call_args
        self.assertEqual(args[0], "POST")
        self.assertTrue(args[1].endswith("/api/v1/invoices/validate"))
        self.assertNotIn("Idempotency-Key", kwargs["headers"])
        self.assertEqual(kwargs["headers"]["X-Stackin-Company"], "C1")
        self.assertEqual(kwargs["json"]["client_name"], "Acme")

    def test_same_body_as_issue(self):
        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(200, {"result": {}})
            _invoice().issue(**_issue_kwargs())
            issued = request.call_args[1]["json"]
            request.return_value = FakeResponse(200, {"valid": True})
            _invoice().validate(**_issue_kwargs())
            validated = request.call_args[1]["json"]

        self.assertEqual(issued, validated)

    def test_422_rules_failed_is_a_result(self):
        finding = {
            "code": "NCM_INVALID",
            "field": "items[0].product.br.ncm",
            "message": "bad",
            "sefaz_rejection": "778",
            "expected": "x",
            "received": "y",
            "fix_url": "https://app/fix",
        }
        blocker = {"code": "CERT", "field": None, "message": "no certificate"}
        body = {
            "valid": False,
            "detail": finding,
            "errors": [finding, blocker],
            "warnings": [],
        }

        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(422, body)
            result = _invoice().validate(**_issue_kwargs())

        self.assertFalse(result.valid)
        self.assertEqual([e.code for e in result.errors], ["NCM_INVALID", "CERT"])
        self.assertEqual(result.errors[0].sefaz_rejection, "778")
        self.assertEqual(result.errors[0].fix_url, "https://app/fix")
        self.assertIsNone(result.errors[1].field)

    def test_pydantic_422_raises(self):
        body = {"detail": [{"loc": ["body", "items"], "msg": "required"}]}

        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(422, body)
            with self.assertRaises(APIError) as caught:
                _invoice().validate(**_issue_kwargs())

        self.assertEqual(caught.exception.status_code, 422)
        self.assertIsNone(caught.exception.code)

    def test_other_statuses_raise(self):
        for status in (401, 404, 429):
            with patch("stackin.core.client.requests.request") as request:
                request.return_value = FakeResponse(status, {"detail": "no"})
                with self.assertRaises(APIError) as caught:
                    _invoice().validate(**_issue_kwargs())
            self.assertEqual(caught.exception.status_code, status)

    def test_local_checks_still_apply(self):
        with self.assertRaises(ValueError):
            _invoice().validate(**{**_issue_kwargs(), "items": []})


class EventsTest(unittest.TestCase):
    def test_received_events_listed(self):
        self.assertIn("received_invoice.stored", EVENTS)
        self.assertIn("received_invoice.full_document", EVENTS)
