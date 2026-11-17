"""Headers a caller adds to identify itself, never over the SDK's own."""

import unittest

from stackin import FiscalReference, Invoice, Taxpayer


class ExtraHeadersTest(unittest.TestCase):
    def test_none_given_sends_exactly_what_it_did(self):
        client = Invoice(base_url="https://sdk.test", api_key="k")
        self.assertEqual(client._headers(), {"Authorization": "Bearer k"})

    def test_they_ride_on_every_request(self):
        client = Invoice(
            base_url="https://sdk.test",
            api_key="k",
            headers={"X-Stackin-Tool": "list_invoices"},
        )
        self.assertEqual(
            client._headers("idem"),
            {
                "X-Stackin-Tool": "list_invoices",
                "Authorization": "Bearer k",
                "Idempotency-Key": "idem",
            },
        )

    def test_the_sdks_own_headers_always_win(self):
        client = Invoice(
            base_url="https://sdk.test",
            api_key="k",
            company="c-1",
            headers={
                "Authorization": "Bearer forged",
                "X-Stackin-Company": "other",
            },
        )
        headers = client._headers()
        self.assertEqual(headers["Authorization"], "Bearer k")
        self.assertEqual(headers["X-Stackin-Company"], "c-1")

    def test_the_lookup_clients_take_them_too(self):
        for cls in (FiscalReference, Taxpayer):
            with self.subTest(cls.__name__):
                client = cls(
                    base_url="https://sdk.test",
                    api_key="k",
                    headers={"X-Stackin-Tool": "lookup"},
                )
                self.assertEqual(client._headers()["X-Stackin-Tool"], "lookup")

    def test_the_given_dict_is_not_shared(self):
        given = {"X-Stackin-Tool": "a"}
        client = Invoice(base_url="https://sdk.test", api_key="k", headers=given)
        given["X-Stackin-Tool"] = "b"
        self.assertEqual(client._headers()["X-Stackin-Tool"], "a")
