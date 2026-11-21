"""Company.update: what PATCH /company receives, and what it refuses first."""

import unittest
from typing import Any
from unittest.mock import patch

from stackin import APIError, Company, InsufficientPermissionError
from stackin.core.client import COMPANY_HEADER
from tests.test_reference import FakeResponse

BASE = "https://sdk.test/api/v1"


def _company():
    return Company(base_url="https://sdk.test", api_key="k")


def _sent(call, status=200, payload=None, headers=None):
    with patch("stackin.core.client.requests.request") as request:
        request.return_value = FakeResponse(
            status, payload if payload is not None else {}, headers
        )
        result = call(_company())
    return request.call_args, result


class UpdateTest(unittest.TestCase):
    def test_both_groups_in_snake_case(self):
        (args, kwargs), _ = _sent(
            lambda c: c.update(
                address={
                    "street": "Av. Paulista",
                    "number": "1000",
                    "neighborhood": "Bela Vista",
                    "municipality_code": "3550308",
                    "municipality_name": "São Paulo",
                    "zip_code": "01310100",
                },
                fiscal_fields={
                    "tax_regime": "1",
                    "simples_nacional": "3",
                    "simples_apuracao": "1",
                    "state_registration": "ISENTO",
                    "service_code": "01.07.00",
                },
            )
        )

        self.assertEqual(args[:2], ("PATCH", f"{BASE}/company"))
        self.assertEqual(
            kwargs["json"],
            {
                "address": {
                    "street": "Av. Paulista",
                    "number": "1000",
                    "neighborhood": "Bela Vista",
                    "municipality_code": "3550308",
                    "municipality_name": "São Paulo",
                    "zip_code": "01310100",
                },
                "fiscal_fields": {
                    "tax_regime": "1",
                    "simples_nacional": "3",
                    "simples_apuracao": "1",
                    "state_registration": "ISENTO",
                    "service_code": "01.07.00",
                },
            },
        )

    def test_only_given_keys_are_sent(self):
        (_, kwargs), _ = _sent(
            lambda c: c.update(address={"street": "Rua A", "number": None})
        )

        self.assertEqual(kwargs["json"], {"address": {"street": "Rua A"}})

    def test_zip_mask_is_stripped(self):
        (_, kwargs), _ = _sent(lambda c: c.update(address={"zip_code": "01.310-100"}))

        self.assertEqual(kwargs["json"], {"address": {"zip_code": "01310100"}})

    def test_an_empty_group_is_not_sent(self):
        (_, kwargs), _ = _sent(
            lambda c: c.update(address={}, fiscal_fields={"tax_regime": None})
        )

        self.assertEqual(kwargs["json"], {})

    def test_nothing_sends_an_empty_body(self):
        (args, kwargs), _ = _sent(lambda c: c.update())

        self.assertEqual(args[:2], ("PATCH", f"{BASE}/company"))
        self.assertEqual(kwargs["json"], {})

    def test_company_per_call(self):
        (_, kwargs), _ = _sent(
            lambda c: c.update(address={"street": "Rua A"}, company="c-1")
        )

        self.assertEqual(kwargs["headers"][COMPANY_HEADER], "c-1")

    def test_response_is_returned_untouched(self):
        answer = {
            "ready": True,
            "missing": [],
            "by_document_type": {"nfse": {"ready": True}},
            "fix_url": None,
            "address": {"street": "Rua A", "state": "SP"},
            "fiscal_fields": {"tax_regime": "1"},
        }

        _, result = _sent(lambda c: c.update(), payload=answer)

        self.assertEqual(result, answer)

    def test_refusals_before_the_call(self):
        cases: dict[str, dict[str, Any]] = {
            "complement": {"address": {"complement": "Sala 1"}},
            "state": {"address": {"state": "SP"}},
            "unknown fiscal": {"fiscal_fields": {"crt": "1"}},
            "municipality_code": {"address": {"municipality_code": "355030"}},
            "zip_code": {"address": {"zip_code": "0131010"}},
            "tax_regime": {"fiscal_fields": {"tax_regime": "5"}},
            "simples_nacional": {"fiscal_fields": {"simples_nacional": "4"}},
            "simples_apuracao": {"fiscal_fields": {"simples_apuracao": "0"}},
        }
        for message, kwargs in cases.items():
            with self.subTest(message):
                with patch("stackin.core.client.requests.request") as request:
                    with self.assertRaises(ValueError):
                        _company().update(**kwargs)
                    request.assert_not_called()

    def test_unknown_key_names_the_allowed_ones(self):
        with self.assertRaises(ValueError) as caught:
            _company().update(address={"complement": "Sala 1"})

        self.assertIn("complement", str(caught.exception))
        self.assertIn("municipality_code", str(caught.exception))


class RefusalTest(unittest.TestCase):
    def test_forbidden_is_an_api_error(self):
        with self.assertRaises(APIError) as caught:
            _sent(
                lambda c: c.update(fiscal_fields={"tax_regime": "1"}),
                403,
                {"detail": "only the owner may change fiscal_fields"},
            )

        self.assertEqual(caught.exception.status_code, 403)
        self.assertNotIsInstance(caught.exception, InsufficientPermissionError)

    def test_missing_scope_is_insufficient_permission(self):
        with self.assertRaises(InsufficientPermissionError):
            _sent(
                lambda c: c.update(address={"street": "Rua A"}),
                403,
                {
                    "detail": {
                        "code": "INSUFFICIENT_PERMISSION",
                        "message": "needs company:write",
                    }
                },
            )

    def test_reference_unavailable_is_an_api_error(self):
        with self.assertRaises(APIError) as caught:
            _sent(
                lambda c: c.update(address={"municipality_code": "3550308"}),
                503,
                {"detail": "retry"},
                {"Retry-After": "30"},
            )

        self.assertEqual(caught.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
