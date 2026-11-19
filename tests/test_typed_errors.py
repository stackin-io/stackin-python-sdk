"""The typed refusals: 402, 429 and a saved client that cannot be used."""

import unittest
from unittest.mock import patch

from stackin import (
    APIError,
    ClientInactiveError,
    ClientNotFoundError,
    DocumentType,
    Invoice,
    PaymentRequiredError,
    RateLimitedError,
)
from stackin.br import Product
from stackin.core.exceptions import _api_error
from tests.test_reference import FakeResponse

CLIENT_ID = "0b6c3d1e-7a2f-4e59-9c10-5d8e2f3a4b6c"


def _invoice():
    return Invoice(base_url="https://sdk.test", api_key="k")


def _raised(status, payload, headers=None):
    with patch("stackin.core.client.requests.request") as request:
        request.return_value = FakeResponse(status, payload, headers)
        try:
            _invoice().consult("KEY", document_type=DocumentType.NFE)
        except APIError as error:
            return error
    raise AssertionError("no APIError raised")


class TypedErrorsTest(unittest.TestCase):
    def test_402_is_payment_required(self):
        error = _raised(402, {"detail": "No credit left."})

        self.assertIsInstance(error, PaymentRequiredError)
        self.assertIsInstance(error, APIError)
        self.assertEqual(error.detail, "No credit left.")

    def test_any_429_is_rate_limited(self):
        error = _raised(429, {"detail": "Too many"}, {"retry-after": "7"})

        self.assertIsInstance(error, RateLimitedError)
        self.assertEqual(error.retry_after, 7)
        self.assertIsNone(error.retry_at)
        self.assertIsNone(error.code)

    def test_429_without_header_or_body(self):
        error = _api_error(429, "slow down")

        assert isinstance(error, RateLimitedError)
        self.assertIsNone(error.retry_after)

    def test_unparseable_retry_values_are_none(self):
        error = _api_error(
            429,
            "x",
            {"retry_at": "tomorrow", "code": "X"},
            {"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"},
        )

        assert isinstance(error, RateLimitedError)
        self.assertIsNone(error.retry_after)
        self.assertIsNone(error.retry_at)
        self.assertEqual(error.code, "X")

    def test_client_inactive(self):
        detail = {
            "code": "CLIENT_INACTIVE",
            "message": "Client is inactive.",
            "client_id": CLIENT_ID,
        }

        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(422, {"detail": detail})
            with self.assertRaises(ClientInactiveError) as caught:
                _invoice().issue(
                    document_type=DocumentType.NFSE,
                    client_id=CLIENT_ID,
                    items=[Product(description="Service", unit_price="10")],
                )

        self.assertEqual(caught.exception.client_id, CLIENT_ID)
        self.assertEqual(caught.exception.status_code, 422)

    def test_client_not_found(self):
        detail = {
            "code": "CLIENT_NOT_FOUND",
            "message": "Client not found.",
            "client_id": CLIENT_ID,
        }

        error = _raised(404, {"detail": detail})

        self.assertIsInstance(error, ClientNotFoundError)
        self.assertEqual(error.client_id, CLIENT_ID)

    def test_other_422_and_404_stay_plain(self):
        self.assertIs(type(_raised(404, {"detail": "Not found"})), APIError)
        self.assertIs(type(_raised(422, {"detail": {"code": "OTHER"}})), APIError)


if __name__ == "__main__":
    unittest.main()
