"""Usage, the received documents' sync and the history filters."""

import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from stackin import Invoice, RateLimitedError, ReceivedSync, Usage
from tests.test_reference import FakeResponse

BASE = "https://sdk.test/api/v1"

USAGE = {
    "plan_name": "Pro",
    "plan_slug": "pro",
    "included_invoices": 500,
    "used_invoices": 12,
    "overage_price_cents": 15,
    "included_received": 50,
    "used_received": 7,
    "received_price_cents": 5,
    "received_free": True,
    "current_period_start": "2026-11-01T00:00:00",
    "current_period_end": "2026-12-01T00:00:00",
    "credit_balance": 4200,
    "companies_on_account": 2,
}

COOLDOWN = {
    "detail": "The SEFAZ allows the next read after 2026-11-18T22:00:00Z.",
    "code": "DISTRIBUTION_COOLDOWN",
    "retry_at": "2026-11-18T22:00:00Z",
}


def _invoice():
    return Invoice(base_url="https://sdk.test", api_key="k")


def _call(call, status=200, payload=None, headers=None):
    with patch("stackin.core.client.requests.request") as request:
        request.return_value = FakeResponse(status, payload, headers)
        result = call(_invoice())
    return request.call_args, result


class UsageTest(unittest.TestCase):
    def test_gets_the_company_usage(self):
        (args, kwargs), usage = _call(lambda c: c.usage(), payload=USAGE)

        self.assertEqual(args[:2], ("GET", f"{BASE}/company/usage"))
        self.assertIsNone(kwargs["json"])
        self.assertIsInstance(usage, Usage)
        self.assertEqual(usage.plan_slug, "pro")
        self.assertEqual(usage.used_invoices, 12)
        self.assertEqual(usage.overage_price_cents, 15)
        self.assertTrue(usage.received_free)
        self.assertEqual(usage.credit_balance, 4200)
        self.assertEqual(usage.current_period_start, datetime(2026, 11, 1))
        self.assertEqual(usage.companies_on_account, 2)

    def test_unknown_fields_are_ignored(self):
        _, usage = _call(lambda c: c.usage(), payload={**USAGE, "added_later": "x"})

        self.assertFalse(hasattr(usage, "added_later"))

    def test_received_fields_default_when_absent(self):
        older = {
            key: value
            for key, value in USAGE.items()
            if not key.endswith("_received")
            and key not in ("received_price_cents", "received_free")
        }

        _, usage = _call(lambda c: c.usage(), payload=older)

        self.assertEqual(usage.included_received, 50)
        self.assertEqual(usage.used_received, 0)
        self.assertEqual(usage.received_price_cents, 5)
        self.assertFalse(usage.received_free)

    def test_null_overage_and_open_period(self):
        payload = {
            **USAGE,
            "overage_price_cents": None,
            "current_period_end": None,
        }

        _, usage = _call(lambda c: c.usage(), payload=payload)

        self.assertIsNone(usage.overage_price_cents)
        self.assertIsNone(usage.current_period_end)

    def test_sends_the_company(self):
        (_, kwargs), _ = _call(lambda c: c.usage(company="X"), payload=USAGE)

        self.assertEqual(kwargs["headers"]["X-Stackin-Company"], "X")


class SyncReceivedTest(unittest.TestCase):
    def test_posts_without_a_body(self):
        payload = {
            "stored": 3,
            "pages": 1,
            "last_nsu": "000000000000123",
            "max_nsu": "000000000000123",
            "next_sync_at": "2026-11-18T22:00:00",
        }

        (args, kwargs), result = _call(lambda c: c.sync_received(), payload=payload)

        self.assertEqual(args[:2], ("POST", f"{BASE}/received-invoices/sync"))
        self.assertIsNone(kwargs["json"])
        self.assertIsInstance(result, ReceivedSync)
        self.assertEqual(result.stored, 3)
        self.assertEqual(result.pages, 1)
        self.assertEqual(result.last_nsu, "000000000000123")
        self.assertEqual(result.next_sync_at, datetime(2026, 11, 18, 22))

    def test_nulls_and_unknown_fields(self):
        payload = {
            "stored": 0,
            "pages": 0,
            "last_nsu": "0",
            "max_nsu": None,
            "next_sync_at": None,
            "added_later": 1,
        }

        _, result = _call(lambda c: c.sync_received(), payload=payload)

        self.assertIsNone(result.max_nsu)
        self.assertIsNone(result.next_sync_at)

    def test_cooldown_raises_rate_limited(self):
        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(429, COOLDOWN, {"Retry-After": "1800"})
            with self.assertRaises(RateLimitedError) as caught:
                _invoice().sync_received()

        error = caught.exception
        self.assertEqual(error.status_code, 429)
        self.assertEqual(error.code, "DISTRIBUTION_COOLDOWN")
        self.assertEqual(error.retry_after, 1800)
        self.assertEqual(
            error.retry_at, datetime(2026, 11, 18, 22, tzinfo=timezone.utc)
        )
        self.assertEqual(error.detail, COOLDOWN["detail"])


class HistoryFiltersTest(unittest.TestCase):
    def test_external_reference_and_summary(self):
        (_, kwargs), _ = _call(
            lambda c: c.history(external_reference="order-42", fields="summary")
        )

        self.assertEqual(
            kwargs["params"],
            {"external_reference": "order-42", "fields": "summary"},
        )

    def test_left_out_when_unset(self):
        (_, kwargs), _ = _call(lambda c: c.history())

        self.assertNotIn("external_reference", kwargs["params"])
        self.assertNotIn("fields", kwargs["params"])


if __name__ == "__main__":
    unittest.main()
