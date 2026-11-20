"""The webhook endpoint registry and its delivery log."""

import unittest
from unittest.mock import patch

from stackin import EVENTS, APIError, Webhooks
from tests.test_reference import FakeResponse

BASE = "https://sdk.test/api/v1"
ENDPOINT_ID = "1d2c3b4a-5968-7766-5544-332211009f0e"
SECRET = "s" * 32


def _hooks():
    return Webhooks(base_url="https://sdk.test", api_key="k")


def _sent(call, status=200, payload=None):
    with patch("stackin.core.client.requests.request") as request:
        request.return_value = FakeResponse(
            status, payload if payload is not None else {}
        )
        result = call(_hooks())
    return request.call_args, result


class CreateTest(unittest.TestCase):
    def test_minimal_body(self):
        (args, kwargs), _ = _sent(
            lambda c: c.create(url="https://shop.test/hook", secret=SECRET),
            201,
        )

        self.assertEqual(args[:2], ("POST", f"{BASE}/webhooks"))
        self.assertEqual(
            kwargs["json"], {"url": "https://shop.test/hook", "secret": SECRET}
        )

    def test_events_go_out_as_a_list(self):
        (_, kwargs), _ = _sent(
            lambda c: c.create(
                url="https://shop.test/hook",
                secret=SECRET,
                events=("invoice.authorized", "invoice.rejected"),
            )
        )

        self.assertEqual(
            kwargs["json"]["events"],
            ["invoice.authorized", "invoice.rejected"],
        )

    def test_events_match_the_api(self):
        self.assertEqual(
            EVENTS,
            (
                "invoice.authorized",
                "invoice.rejected",
                "invoice.cancelled",
                "invoice.corrected",
            ),
        )

    def test_refusals_before_the_call(self):
        cases = {
            "url": dict(url="http://shop.test/hook", secret=SECRET),
            "secret": dict(url="https://shop.test/hook", secret="short"),
            "unknown events": dict(
                url="https://shop.test/hook",
                secret=SECRET,
                events=["invoice.paid"],
            ),
            "list of event": dict(
                url="https://shop.test/hook",
                secret=SECRET,
                events="invoice.authorized",
            ),
        }
        for message, kwargs in cases.items():
            with (
                self.subTest(message),
                patch("stackin.core.client.requests.request") as request,
                self.assertRaisesRegex(ValueError, message),
            ):
                _hooks().create(**kwargs)
            request.assert_not_called()

    def test_the_secret_is_not_echoed_in_the_error(self):
        with self.assertRaises(ValueError) as caught:
            _hooks().create(url="https://shop.test/hook", secret="short-secret")

        self.assertNotIn("short-secret", str(caught.exception))


class ListTest(unittest.TestCase):
    def test_returns_the_plain_list(self):
        rows = [{"id": ENDPOINT_ID, "url": "https://shop.test/hook"}]
        (args, _), result = _sent(lambda c: c.list(), payload=rows)

        self.assertEqual(args[:2], ("GET", f"{BASE}/webhooks"))
        self.assertEqual(result, rows)

    def test_company_names_the_header(self):
        (_, kwargs), _ = _sent(lambda c: c.list(company="acme"), payload=[])

        self.assertEqual(kwargs["headers"]["X-Stackin-Company"], "acme")


class DeleteTest(unittest.TestCase):
    def test_deletes_by_id(self):
        (args, _), result = _sent(lambda c: c.delete(ENDPOINT_ID), 204)

        self.assertEqual(args[:2], ("DELETE", f"{BASE}/webhooks/{ENDPOINT_ID}"))
        self.assertIsNone(result)

    def test_the_id_cannot_leave_its_segment(self):
        with self.assertRaises(ValueError):
            _hooks().delete("..")

    def test_unknown_id_is_an_api_error(self):
        with self.assertRaises(APIError) as caught:
            _sent(
                lambda c: c.delete(ENDPOINT_ID),
                404,
                {"detail": "webhook not found"},
            )

        self.assertEqual(caught.exception.status_code, 404)


class DeliveriesTest(unittest.TestCase):
    def test_pagination_goes_out(self):
        (args, kwargs), _ = _sent(lambda c: c.deliveries(limit=5, offset=10))

        self.assertEqual(args[:2], ("GET", f"{BASE}/webhooks/deliveries"))
        self.assertEqual(kwargs["params"], {"limit": 5, "offset": 10})
