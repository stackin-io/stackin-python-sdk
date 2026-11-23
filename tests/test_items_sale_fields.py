import json
import unittest
from decimal import Decimal
from unittest.mock import patch

from stackin import Items
from tests.test_reference import FakeResponse


def _items():
    return Items(base_url="https://sdk.test", api_key="k")


def _body(call, status=200):
    with patch("stackin.core.client.requests.request") as request:
        request.return_value = FakeResponse(status, {})
        call(_items())
    return request.call_args.kwargs["json"]


class CreateTest(unittest.TestCase):
    def test_unset_fields_are_not_sent(self):
        body = _body(lambda c: c.create(kind="product", description="Cafe"))

        for key in ("net_weight", "gross_weight", "ibs_cbs_cst", "ibs_cbs_class"):
            self.assertNotIn(key, body)

    def test_the_new_fields_go_out_by_their_api_names(self):
        body = _body(
            lambda c: c.create(
                kind="product",
                description="Cafe",
                net_weight=Decimal("0.350"),
                gross_weight="0.4",
                ibs_cbs_cst="000",
                ibs_cbs_class="000001",
            )
        )

        self.assertEqual((body["net_weight"], body["gross_weight"]), ("0.350", "0.4"))
        self.assertEqual(
            (body["ibs_cbs_cst"], body["ibs_cbs_class"]), ("000", "000001")
        )
        json.dumps(body)

    def test_upsert_sends_them_too(self):
        body = _body(
            lambda c: c.upsert(
                kind="product",
                description="Cafe",
                net_weight=Decimal("1"),
            )
        )

        self.assertEqual(body["net_weight"], "1")

    def test_a_zero_weight_is_sent(self):
        body = _body(lambda c: c.create(kind="product", description="x", net_weight=0))

        self.assertEqual(body["net_weight"], 0)

    def test_weights_take_six_decimals(self):
        body = _body(
            lambda c: c.create(
                kind="product", description="x", net_weight=Decimal("0.123456")
            )
        )

        self.assertEqual(body["net_weight"], "0.123456")
        with self.assertRaisesRegex(ValueError, "net_weight"):
            _items().create(
                kind="product", description="x", net_weight=Decimal("0.1234567")
            )
        with self.assertRaisesRegex(ValueError, "gross_weight"):
            _items().update("abc", gross_weight=Decimal("0.1234567"))

    def test_negative_weights_are_refused(self):
        with self.assertRaisesRegex(ValueError, "net_weight"):
            _items().create(kind="product", description="x", net_weight=-1)
        with self.assertRaisesRegex(ValueError, "gross_weight"):
            _items().create(kind="product", description="x", gross_weight=-1)


class UpdateTest(unittest.TestCase):
    def test_only_the_passed_fields_are_sent(self):
        body = _body(lambda c: c.update("abc", net_weight=Decimal("2.5")))

        self.assertEqual(body, {"net_weight": "2.5"})

    def test_none_clears_a_field(self):
        body = _body(
            lambda c: c.update(
                "abc", gross_weight=None, ibs_cbs_cst=None, ibs_cbs_class=None
            )
        )

        self.assertEqual(
            body,
            {"gross_weight": None, "ibs_cbs_cst": None, "ibs_cbs_class": None},
        )

    def test_update_refuses_a_bad_weight(self):
        with self.assertRaisesRegex(ValueError, "net_weight"):
            _items().update("abc", net_weight=Decimal("-1"))
