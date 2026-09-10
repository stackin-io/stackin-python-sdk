"""The registry lookup, and the search it must never grow."""

import unittest
from unittest.mock import patch

from stackin import Taxpayer
from stackin.core.exceptions import APIError
from tests.test_reference import FakeResponse


def _client():
    return Taxpayer(base_url="https://sdk.test", api_key="k")


class GetTest(unittest.TestCase):
    def test_it_looks_up_the_exact_tax_id(self):
        client = _client()

        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(payload={"name": "ACME"})
            client.get("00000000000191")

        args, kwargs = request.call_args
        self.assertEqual(args[0], "GET")
        self.assertEqual(
            args[1], "https://sdk.test/api/v1/taxpayers/00000000000191"
        )
        self.assertEqual(kwargs["params"], {"country": "BR"})

    def test_an_unknown_tax_id_is_an_api_error(self):
        client = _client()

        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(404, {"detail": "no"})

            with self.assertRaises(APIError):
                client.get("00000000000000")

    def test_one_call_can_override_the_country(self):
        client = _client()

        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(payload={})
            client.get("1", country="AR")

        self.assertEqual(request.call_args.kwargs["params"]["country"], "AR")


class SurfaceTest(unittest.TestCase):
    def test_it_offers_exactly_one_public_method(self):
        """A search here would be a bulk export of real people.

        The API refuses it at the route, but that is the smaller
        reason: this type is thin on purpose, and this test is what
        keeps a well-meaning "parity with FiscalReference" out.
        """
        public = [name for name in dir(Taxpayer) if not name.startswith("_")]

        self.assertEqual(public, ["get"])


if __name__ == "__main__":
    unittest.main()
