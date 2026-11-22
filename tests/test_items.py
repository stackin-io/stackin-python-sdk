"""The item catalog, issuing from it, and its typed refusals."""

import json
import unittest
from decimal import Decimal
from unittest.mock import patch

from pydantic import ValidationError

from stackin import (
    APIError,
    DocumentType,
    Invoice,
    ItemAlreadyExistsError,
    ItemInactiveError,
    ItemKindMismatchError,
    ItemNotFoundError,
    Items,
    ItemSaved,
    ItemTaxRegimeMismatchError,
    ItemTaxRequiredError,
)
from stackin.br import Product
from tests.test_reference import FakeResponse

ITEM_ID = "5c1f0e2a-3b7d-4a96-8e41-9d2c7b6a1f03"
BASE = "https://sdk.test/api/v1"
SECRET = "sk_live_do_not_leak"


def _items(**kwargs):
    return Items(base_url="https://sdk.test", api_key="k", **kwargs)


def _sent(call, client, status=200, payload=None):
    with patch("stackin.core.client.requests.request") as request:
        request.return_value = FakeResponse(status, payload or {})
        result = call(client)
    return request.call_args, result


class ListTest(unittest.TestCase):
    def test_no_filter_sends_no_params(self):
        (args, kwargs), _ = _sent(lambda c: c.list(), _items())

        self.assertEqual(args[:2], ("GET", f"{BASE}/items"))
        self.assertEqual(kwargs["params"], {})
        self.assertIsNone(kwargs["json"])

    def test_every_filter_goes_out_by_its_api_name(self):
        (_, kwargs), _ = _sent(
            lambda c: c.list(
                kind="product",
                search="cafe",
                source="nuvemshop",
                is_active=False,
                limit=10,
                offset=20,
                sort_by="unit_price",
                order_by="desc",
            ),
            _items(),
        )

        self.assertEqual(
            kwargs["params"],
            {
                "kind": "product",
                "search": "cafe",
                "source": "nuvemshop",
                "is_active": "false",
                "limit": 10,
                "offset": 20,
                "sort_by": "unit_price",
                "order_by": "desc",
            },
        )

    def test_is_active_true_is_sent_lowercase(self):
        (_, kwargs), _ = _sent(lambda c: c.list(is_active=True), _items())

        self.assertEqual(kwargs["params"], {"is_active": "true"})

    def test_it_returns_the_page_as_sent(self):
        page = {"data": [{"id": ITEM_ID}], "total": 1}
        _, result = _sent(lambda c: c.list(), _items(), payload=page)

        self.assertEqual(result, page)

    def test_company_names_the_header_for_the_call(self):
        (_, kwargs), _ = _sent(lambda c: c.list(company="ACME"), _items())

        self.assertEqual(kwargs["headers"]["X-Stackin-Company"], "ACME")


class GetTest(unittest.TestCase):
    def test_it_reads_one_item_by_id(self):
        (args, kwargs), _ = _sent(lambda c: c.get(ITEM_ID), _items())

        self.assertEqual(args[:2], ("GET", f"{BASE}/items/{ITEM_ID}"))
        self.assertIsNone(kwargs["json"])

    def test_an_id_cannot_leave_its_segment(self):
        for bad in ("..", ".", ""):
            with self.assertRaises(ValueError):
                _items().get(bad)

    def test_a_slash_in_an_id_is_escaped(self):
        (args, _), _ = _sent(lambda c: c.get("a/b"), _items())

        self.assertEqual(args[1], f"{BASE}/items/a%2Fb")


class CreateTest(unittest.TestCase):
    def test_only_the_fields_given_are_sent(self):
        (args, kwargs), _ = _sent(
            lambda c: c.create(kind="service", description="Consultoria"),
            _items(),
            201,
        )

        self.assertEqual(args[:2], ("POST", f"{BASE}/items"))
        self.assertEqual(
            kwargs["json"], {"kind": "service", "description": "Consultoria"}
        )

    def test_every_field_goes_out_by_its_api_name(self):
        (_, kwargs), _ = _sent(
            lambda c: c.create(
                kind="product",
                description="Cafe torrado 500g",
                code="CAF-500",
                unit_price=18.9,
                unit="UN",
                external_reference="ns-variant-1",
                notes="n",
                ncm="09012100",
                cfop="5102",
                tax_situation="102",
                origin="0",
                cest="1709600",
                gtin="7891000315507",
                source="nuvemshop",
            ),
            _items(),
            201,
        )

        self.assertEqual(
            kwargs["json"],
            {
                "kind": "product",
                "description": "Cafe torrado 500g",
                "code": "CAF-500",
                "unit_price": 18.9,
                "unit": "UN",
                "external_reference": "ns-variant-1",
                "notes": "n",
                "ncm": "09012100",
                "cfop": "5102",
                "tax_situation": "102",
                "origin": "0",
                "cest": "1709600",
                "gtin": "7891000315507",
                "source": "nuvemshop",
            },
        )

    def test_a_service_sends_its_own_fields(self):
        (_, kwargs), _ = _sent(
            lambda c: c.create(
                kind="service",
                description="Consultoria",
                service_code="1.07",
                iss_retained=False,
            ),
            _items(),
            201,
        )

        self.assertEqual(kwargs["json"]["service_code"], "1.07")
        self.assertIs(kwargs["json"]["iss_retained"], False)

    def test_a_decimal_price_keeps_every_place(self):
        (_, kwargs), _ = _sent(
            lambda c: c.create(
                kind="product",
                description="Parafuso",
                unit_price=Decimal("0.0000012345"),
            ),
            _items(),
            201,
        )

        self.assertEqual(kwargs["json"]["unit_price"], "0.0000012345")

    def test_create_returns_the_item(self):
        item = {"id": ITEM_ID, "kind": "service"}
        _, result = _sent(
            lambda c: c.create(kind="service", description="x"),
            _items(),
            200,
            item,
        )

        self.assertEqual(result, item)

    def test_upsert_says_201_is_created(self):
        _, saved = _sent(
            lambda c: c.upsert(kind="service", description="x"),
            _items(),
            201,
            {"id": ITEM_ID},
        )

        self.assertIsInstance(saved, ItemSaved)
        self.assertTrue(saved.created)
        self.assertEqual(saved.item["id"], ITEM_ID)

    def test_upsert_says_200_is_updated(self):
        _, saved = _sent(
            lambda c: c.upsert(kind="service", description="x"),
            _items(),
            200,
            {"id": ITEM_ID},
        )

        self.assertFalse(saved.created)
        self.assertEqual(saved.item["id"], ITEM_ID)


class UpdateTest(unittest.TestCase):
    def test_only_the_arguments_passed_are_sent(self):
        (args, kwargs), _ = _sent(
            lambda c: c.update(ITEM_ID, description="Novo"), _items()
        )

        self.assertEqual(args[:2], ("PATCH", f"{BASE}/items/{ITEM_ID}"))
        self.assertEqual(kwargs["json"], {"description": "Novo"})

    def test_none_clears_a_field(self):
        (_, kwargs), _ = _sent(
            lambda c: c.update(ITEM_ID, notes=None, ncm=None), _items()
        )

        self.assertEqual(kwargs["json"], {"notes": None, "ncm": None})

    def test_false_and_zero_are_not_mistaken_for_unset(self):
        (_, kwargs), _ = _sent(
            lambda c: c.update(
                ITEM_ID, is_active=False, iss_retained=False, unit_price=0
            ),
            _items(),
        )

        self.assertEqual(
            kwargs["json"],
            {"is_active": False, "iss_retained": False, "unit_price": 0},
        )

    def test_nothing_passed_sends_an_empty_body(self):
        (_, kwargs), _ = _sent(lambda c: c.update(ITEM_ID), _items())

        self.assertEqual(kwargs["json"], {})

    def test_source_is_not_an_update_argument(self):
        with self.assertRaises(TypeError):
            _items().update(ITEM_ID, source="manual")

    def test_an_id_cannot_leave_its_segment(self):
        with self.assertRaises(ValueError):
            _items().update("..", notes="x")


class DeactivateTest(unittest.TestCase):
    def test_it_sends_a_delete_and_returns_nothing(self):
        (args, _), result = _sent(lambda c: c.deactivate(ITEM_ID), _items(), 204)

        self.assertEqual(args[:2], ("DELETE", f"{BASE}/items/{ITEM_ID}"))
        self.assertIsNone(result)

    def test_a_204_body_is_never_decoded(self):
        response = FakeResponse(204)
        response.content = b""

        def boom():
            raise AssertionError("a 204 has no body to decode")

        response.json = boom  # type: ignore[method-assign]
        with patch("stackin.core.client.requests.request", return_value=response):
            self.assertIsNone(_items().deactivate(ITEM_ID))

    def test_an_id_cannot_leave_its_segment(self):
        with self.assertRaises(ValueError):
            _items().deactivate("..")


class ReactivateTest(unittest.TestCase):
    def test_it_patches_is_active_true_and_returns_the_item(self):
        item = {"id": ITEM_ID, "is_active": True}
        (args, kwargs), result = _sent(
            lambda c: c.reactivate(ITEM_ID), _items(), payload=item
        )

        self.assertEqual(args[:2], ("PATCH", f"{BASE}/items/{ITEM_ID}"))
        self.assertEqual(kwargs["json"], {"is_active": True})
        self.assertEqual(result, item)


class KeyTest(unittest.TestCase):
    def test_the_key_is_only_in_the_authorization_header(self):
        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(200, {})
            Items(base_url="https://sdk.test", api_key=SECRET).list()
        args, kwargs = request.call_args

        self.assertEqual(kwargs["headers"]["Authorization"], f"Bearer {SECRET}")
        self.assertNotIn(
            SECRET, json.dumps([args[:2], kwargs["params"], kwargs["json"]])
        )

    def test_the_key_is_not_in_an_error(self):
        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(
                404, {"detail": {"code": "ITEM_NOT_FOUND", "item_id": ITEM_ID}}
            )
            with self.assertRaises(ItemNotFoundError) as caught:
                Items(base_url="https://sdk.test", api_key=SECRET).get(ITEM_ID)

        self.assertNotIn(SECRET, str(caught.exception))
        self.assertNotIn(SECRET, repr(caught.exception))


def _refused(status, detail, call=None):
    with patch("stackin.core.client.requests.request") as request:
        request.return_value = FakeResponse(status, {"detail": detail})
        try:
            (call or (lambda c: c.get(ITEM_ID)))(_items())
        except APIError as error:
            return error
    raise AssertionError("no APIError raised")


class ErrorsTest(unittest.TestCase):
    def test_409_item_exists_names_the_item_and_field(self):
        error = _refused(
            409,
            {"code": "ITEM_EXISTS", "item_id": ITEM_ID, "field": "code"},
            lambda c: c.create(kind="service", description="x"),
        )

        self.assertIsInstance(error, ItemAlreadyExistsError)
        self.assertIsInstance(error, APIError)
        assert isinstance(error, ItemAlreadyExistsError)
        self.assertEqual(error.item_id, ITEM_ID)
        self.assertEqual(error.field, "code")
        self.assertEqual(error.status_code, 409)

    def test_404_item_not_found(self):
        error = _refused(404, {"code": "ITEM_NOT_FOUND", "item_id": ITEM_ID})

        assert isinstance(error, ItemNotFoundError)
        self.assertEqual(error.item_id, ITEM_ID)

    def test_422_item_inactive(self):
        error = _refused(422, {"code": "ITEM_INACTIVE", "item_id": ITEM_ID})

        assert isinstance(error, ItemInactiveError)
        self.assertEqual(error.item_id, ITEM_ID)

    def test_422_kind_mismatch_carries_the_line(self):
        error = _refused(
            422, {"code": "ITEM_KIND_MISMATCH", "item_id": ITEM_ID, "index": 2}
        )

        assert isinstance(error, ItemKindMismatchError)
        self.assertEqual((error.item_id, error.index), (ITEM_ID, 2))

    def test_kind_mismatch_without_an_index(self):
        error = _refused(422, {"code": "ITEM_KIND_MISMATCH", "item_id": ITEM_ID})

        assert isinstance(error, ItemKindMismatchError)
        self.assertIsNone(error.index)

    def test_422_tax_required(self):
        error = _refused(422, {"code": "ITEM_TAX_REQUIRED", "item_id": ITEM_ID})

        assert isinstance(error, ItemTaxRequiredError)
        self.assertEqual(error.item_id, ITEM_ID)

    def test_422_tax_regime_mismatch(self):
        error = _refused(
            422,
            {
                "code": "ITEM_TAX_REGIME_MISMATCH",
                "message": "CSOSN on a CRT 3 company",
                "item_id": ITEM_ID,
                "index": 2,
            },
        )

        assert isinstance(error, ItemTaxRegimeMismatchError)
        self.assertEqual(error.item_id, ITEM_ID)
        self.assertEqual(error.index, 2)
        self.assertEqual(error.status_code, 422)

    def test_a_code_on_the_wrong_status_stays_a_plain_apierror(self):
        error = _refused(500, {"code": "ITEM_EXISTS"})

        self.assertIs(type(error), APIError)

    def test_a_422_body_list_stays_a_plain_apierror(self):
        error = _refused(422, [{"loc": ["body", "ncm"], "msg": "bad"}])

        self.assertIs(type(error), APIError)


def _line(**kwargs):
    return Product(**kwargs)


class IssueWithItemTest(unittest.TestCase):
    def setUp(self):
        self.invoice = Invoice(api_key="k")

    def body(self, **call):
        with patch.object(self.invoice, "_request", return_value={}) as sent:
            self.invoice.issue(**call)
        return sent.call_args.kwargs["json"]

    def issue_kwargs(self, document_type, line):
        return {
            "document_type": document_type,
            "client_name": "ACME",
            "tax_id": "11222333000181",
            "items": [line],
        }

    def test_item_id_alone_is_a_valid_nfse_line(self):
        body = self.body(**self.issue_kwargs(DocumentType.NFSE, _line(item_id=ITEM_ID)))

        self.assertEqual(body["items"][0]["item_id"], ITEM_ID)
        self.assertNotIn("description", body["items"][0])

    def test_item_id_alone_is_a_valid_nfe_line_without_ncm_or_cfop(self):
        body = self.body(
            **self.issue_kwargs(DocumentType.NFE, _line(item_id=ITEM_ID)),
            recipient_address=_address(),
        )

        self.assertEqual(body["items"][0]["item_id"], ITEM_ID)

    def test_fields_sent_with_item_id_are_kept_to_win(self):
        body = self.body(
            **self.issue_kwargs(
                DocumentType.NFSE,
                _line(item_id=ITEM_ID, description="Outro", unit_price=Decimal("9.5")),
            )
        )

        line = body["items"][0]
        self.assertEqual(line["item_id"], ITEM_ID)
        self.assertEqual(line["description"], "Outro")
        self.assertEqual(line["unit_price"], "9.5")

    def test_a_line_without_item_id_sends_the_same_keys_as_before(self):
        line = _line(description="Servico", amount=Decimal("10")).to_dict()

        self.assertNotIn("item_id", line)
        self.assertEqual(
            sorted(line),
            [
                "amount",
                "description",
                "discount",
                "observations",
                "product",
                "service_code",
                "tax_retained",
                "unit_price",
            ],
        )
        self.assertNotIn("item_id", line["product"])

    def test_without_item_id_ncm_and_cfop_are_still_required_on_an_nfe(self):
        with self.assertRaises(ValueError):
            self.body(
                **self.issue_kwargs(DocumentType.NFE, _line(description="x", amount=1)),
                recipient_address=_address(),
            )

    def test_without_item_id_the_description_is_still_required(self):
        with self.assertRaises(ValidationError):
            Product(amount=Decimal("1"))

    def test_an_empty_description_is_still_refused(self):
        with self.assertRaises(ValidationError):
            Product(description="", item_id=ITEM_ID)

    def test_an_over_long_nfe_description_is_still_refused_with_item_id(self):
        with self.assertRaises(ValueError):
            self.body(
                **self.issue_kwargs(
                    DocumentType.NFE, _line(item_id=ITEM_ID, description="x" * 121)
                ),
                recipient_address=_address(),
            )

    def test_the_line_round_trips_as_json(self):
        line = _line(item_id=ITEM_ID).to_dict()

        self.assertEqual(json.loads(json.dumps(line))["item_id"], ITEM_ID)


def _address():
    from stackin import Address

    return Address(
        street="Rua das Flores",
        number="100",
        neighborhood="Centro",
        city="Sao Paulo",
        state="SP",
        zip_code="01001000",
        city_code="3550308",
    )


if __name__ == "__main__":
    unittest.main()
