"""What the reference client sends, and what it refuses to send."""

import unittest
from unittest.mock import patch

from stackin import KINDS, FiscalReference, Kind
from stackin.core.exceptions import APIError


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.content = b"{}"
        self.text = ""

    @property
    def ok(self):
        return self.status_code < 400

    def json(self):
        return self._payload


def _client():
    return FiscalReference(base_url="https://sdk.test", api_key="k")


class AccessorsTest(unittest.TestCase):
    def test_every_documented_kind_has_an_accessor(self):
        client = _client()

        for name in KINDS:
            self.assertIsInstance(getattr(client, name), Kind, name)

    def test_a_kind_with_no_accessor_is_still_reachable(self):
        client = _client()

        self.assertEqual(
            client.kind("published_tomorrow").name, "published_tomorrow"
        )


class GetTest(unittest.TestCase):
    def test_it_asks_for_the_one_code(self):
        client = _client()

        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(payload={"code": "84716052"})
            client.ncm.get("84716052")

        args, kwargs = request.call_args
        self.assertEqual(args[0], "GET")
        self.assertEqual(
            args[1], "https://sdk.test/api/v1/fiscal-references/ncm/84716052"
        )
        self.assertEqual(kwargs["params"], {"country": "BR"})

    def test_a_missing_code_is_an_api_error_not_a_new_type(self):
        client = _client()

        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(404, {"detail": "no"})

            with self.assertRaises(APIError) as caught:
                client.cfop.get("9999")

        self.assertEqual(caught.exception.status_code, 404)


class SearchTest(unittest.TestCase):
    def test_it_pins_the_kind_it_was_reached_through(self):
        client = _client()

        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(payload={"data": []})
            client.ncm.search("teclado")

        self.assertEqual(
            request.call_args.kwargs["params"],
            {"country": "BR", "kind": "ncm", "search": "teclado"},
        )

    def test_no_term_is_the_listing(self):
        client = _client()

        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(payload={"data": []})
            client.cfop.search()

        self.assertEqual(
            request.call_args.kwargs["params"],
            {"country": "BR", "kind": "cfop"},
        )

    def test_an_empty_term_is_not_sent_as_an_empty_search(self):
        """The route 422s on search="" — never invent that failure."""
        client = _client()

        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(payload={"data": []})
            client.cfop.search("")

        self.assertNotIn("search", request.call_args.kwargs["params"])

    def test_searching_the_client_itself_pins_no_kind(self):
        client = _client()

        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(payload={"data": []})
            client.search("teclado")

        params = request.call_args.kwargs["params"]
        self.assertNotIn("kind", params)
        self.assertEqual(params["search"], "teclado")

    def test_it_sends_no_sort_by_the_route_would_discard(self):
        client = _client()

        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(payload={"data": []})
            client.ncm.search(limit=10, offset=20)

        params = request.call_args.kwargs["params"]
        self.assertEqual(params["limit"], 10)
        self.assertEqual(params["offset"], 20)
        self.assertNotIn("sort_by", params)
        self.assertNotIn("order_by", params)


class CountryTest(unittest.TestCase):
    def test_it_defaults_to_br(self):
        self.assertEqual(_client().country, "BR")

    def test_the_constructor_sets_it_for_every_accessor(self):
        client = FiscalReference(api_key="k", country="AR")

        self.assertEqual(client.ncm.country, "AR")

    def test_one_call_can_override_it(self):
        client = _client()

        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(payload={})
            client.ncm.get("1", country="PY")

        self.assertEqual(request.call_args.kwargs["params"]["country"], "PY")


class KindsTest(unittest.TestCase):
    def test_it_asks_the_api_rather_than_answering_from_KINDS(self):
        client = _client()

        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(payload=["ncm", "brand_new"])
            result = client.kinds()

        self.assertEqual(
            request.call_args[0][1],
            "https://sdk.test/api/v1/fiscal-references/kinds",
        )
        self.assertIn("brand_new", result)


if __name__ == "__main__":
    unittest.main()


class PathEscapingTest(unittest.TestCase):
    """A code the caller types by hand must not rewrite the path."""

    def test_a_slash_in_a_code_stays_inside_its_segment(self):
        client = _client()

        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(payload={})
            client.ncm.get("8471/60/52")

        self.assertEqual(
            request.call_args[0][1],
            "https://sdk.test/api/v1/fiscal-references/ncm/8471%2F60%2F52",
        )

    def test_a_kind_cannot_climb_out_of_its_endpoint(self):
        """`..` is unreserved, so escaping it is not enough."""
        client = _client()

        with self.assertRaises(ValueError):
            client.kind("..").get("kinds")

    def test_an_empty_code_is_refused_rather_than_dropped(self):
        client = _client()

        with self.assertRaises(ValueError):
            client.ncm.get("")


class ConstructorTest(unittest.TestCase):
    def test_country_is_the_fifth_parameter_not_the_second(self):
        """FiscalReference("https://x", "AR") used to discard "AR"."""
        client = FiscalReference("https://x", None, "k", 30, "AR")

        self.assertEqual(client.country, "AR")
        self.assertEqual(client.ncm.country, "AR")
