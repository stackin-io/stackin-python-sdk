"""The client registry, issuing to a saved client, and its 409."""

import json
import unittest
from decimal import Decimal
from unittest.mock import patch

from stackin import (
    Address,
    APIError,
    ClientAlreadyExistsError,
    Clients,
    DocumentType,
    Invoice,
)
from stackin.br import Product
from tests.test_reference import FakeResponse

CLIENT_ID = "0b6c3d1e-7a2f-4e59-9c10-5d8e2f3a4b6c"
BASE = "https://sdk.test/api/v1"


def _clients(**kwargs):
    return Clients(base_url="https://sdk.test", api_key="k", **kwargs)


def _sent(call, client, status=200, payload=None):
    with patch("stackin.core.client.requests.request") as request:
        request.return_value = FakeResponse(status, payload or {})
        result = call(client)
    return request.call_args, result


class ListTest(unittest.TestCase):
    def test_no_filter_sends_no_params(self):
        (args, kwargs), _ = _sent(lambda c: c.list(), _clients())

        self.assertEqual(args[:2], ("GET", f"{BASE}/clients"))
        self.assertEqual(kwargs["params"], {})
        self.assertIsNone(kwargs["json"])

    def test_every_filter_goes_out_by_its_api_name(self):
        (_, kwargs), _ = _sent(
            lambda c: c.list(
                search="acme",
                source="issued",
                is_active=False,
                limit=10,
                offset=20,
                sort_by="last_used_at",
                order_by="asc",
            ),
            _clients(),
        )

        self.assertEqual(
            kwargs["params"],
            {
                "search": "acme",
                "source": "issued",
                "is_active": "false",
                "limit": 10,
                "offset": 20,
                "sort_by": "last_used_at",
                "order_by": "asc",
            },
        )

    def test_is_active_true_is_sent_lowercase(self):
        (_, kwargs), _ = _sent(lambda c: c.list(is_active=True), _clients())

        self.assertEqual(kwargs["params"], {"is_active": "true"})

    def test_it_returns_the_page_as_sent(self):
        page = {"data": [{"id": CLIENT_ID}], "total": 1}
        _, result = _sent(lambda c: c.list(), _clients(), payload=page)

        self.assertEqual(result, page)


class GetTest(unittest.TestCase):
    def test_it_reads_one_client_by_id(self):
        (args, kwargs), _ = _sent(lambda c: c.get(CLIENT_ID), _clients())

        self.assertEqual(args[:2], ("GET", f"{BASE}/clients/{CLIENT_ID}"))
        self.assertIsNone(kwargs["json"])

    def test_an_id_cannot_leave_its_segment(self):
        with self.assertRaises(ValueError):
            _clients().get("..")


class CreateTest(unittest.TestCase):
    def test_only_the_fields_given_are_sent(self):
        (args, kwargs), _ = _sent(
            lambda c: c.create(name="ACME", tax_id="11.222.333/0001-81"),
            _clients(),
        )

        self.assertEqual(args[:2], ("POST", f"{BASE}/clients"))
        self.assertEqual(
            kwargs["json"], {"name": "ACME", "tax_id": "11.222.333/0001-81"}
        )

    def test_every_field_goes_out_by_its_api_name(self):
        address = Address(
            street="Rua A",
            number="1",
            neighborhood="Centro",
            city="Sao Paulo",
            state="SP",
            zip_code="01001000",
        )
        (_, kwargs), _ = _sent(
            lambda c: c.create(
                name="ACME",
                tax_id="11222333000181",
                state_registration="ISENTO",
                municipal_registration="123",
                email="a@acme.test",
                phone="+5511999999999",
                address=address,
                notes="vip",
            ),
            _clients(),
        )

        self.assertEqual(
            kwargs["json"],
            {
                "name": "ACME",
                "tax_id": "11222333000181",
                "state_registration": "ISENTO",
                "municipal_registration": "123",
                "email": "a@acme.test",
                "phone": "+5511999999999",
                "address": address.to_dict(),
                "notes": "vip",
            },
        )

    def test_a_buyer_abroad_goes_by_foreign_id(self):
        (_, kwargs), _ = _sent(
            lambda c: c.create(
                name="Globex",
                foreign_id="P1234567",
                address={"state": "EX", "country_code": "2496"},
            ),
            _clients(),
        )

        self.assertEqual(
            kwargs["json"],
            {
                "name": "Globex",
                "foreign_id": "P1234567",
                "address": {"state": "EX", "country_code": "2496"},
            },
        )


class UpdateTest(unittest.TestCase):
    def test_only_the_fields_passed_are_sent(self):
        (args, kwargs), _ = _sent(
            lambda c: c.update(CLIENT_ID, email="new@acme.test"), _clients()
        )

        self.assertEqual(args[:2], ("PATCH", f"{BASE}/clients/{CLIENT_ID}"))
        self.assertEqual(kwargs["json"], {"email": "new@acme.test"})

    def test_none_clears_a_field(self):
        (_, kwargs), _ = _sent(
            lambda c: c.update(CLIENT_ID, notes=None, phone=None), _clients()
        )

        self.assertEqual(kwargs["json"], {"phone": None, "notes": None})

    def test_an_address_replaces_the_whole_address(self):
        address = Address(state="RJ", city="Rio de Janeiro")
        (_, kwargs), _ = _sent(
            lambda c: c.update(CLIENT_ID, address=address), _clients()
        )

        self.assertEqual(
            kwargs["json"], {"address": {"state": "RJ", "city": "Rio de Janeiro"}}
        )


class DeactivateTest(unittest.TestCase):
    def test_it_deletes_and_returns_nothing(self):
        (args, kwargs), result = _sent(
            lambda c: c.deactivate(CLIENT_ID), _clients(), status=204
        )

        self.assertEqual(args[:2], ("DELETE", f"{BASE}/clients/{CLIENT_ID}"))
        self.assertIsNone(kwargs["json"])
        self.assertIsNone(result)

    def test_reactivate_patches_is_active(self):
        (args, kwargs), result = _sent(
            lambda c: c.reactivate(CLIENT_ID),
            _clients(),
            payload={"id": CLIENT_ID, "is_active": True},
        )

        self.assertEqual(args[:2], ("PATCH", f"{BASE}/clients/{CLIENT_ID}"))
        self.assertEqual(kwargs["json"], {"is_active": True})
        self.assertEqual(result, {"id": CLIENT_ID, "is_active": True})


class CompanyTest(unittest.TestCase):
    def test_the_clients_company_goes_on_every_call(self):
        calls = [
            lambda c: c.list(),
            lambda c: c.get(CLIENT_ID),
            lambda c: c.create(name="ACME", tax_id="11222333000181"),
            lambda c: c.update(CLIENT_ID, name="ACME"),
            lambda c: c.deactivate(CLIENT_ID),
            lambda c: c.reactivate(CLIENT_ID),
        ]
        for call in calls:
            (_, kwargs), _ = _sent(call, _clients(company="11222333000181"))
            self.assertEqual(kwargs["headers"]["X-Stackin-Company"], "11222333000181")

    def test_one_call_can_name_another_company(self):
        (_, kwargs), _ = _sent(
            lambda c: c.get(CLIENT_ID, company="other"), _clients(company="mine")
        )

        self.assertEqual(kwargs["headers"]["X-Stackin-Company"], "other")

    def test_no_company_sends_no_header(self):
        (_, kwargs), _ = _sent(lambda c: c.list(), _clients())

        self.assertNotIn("X-Stackin-Company", kwargs["headers"])


DUPLICATE = {
    "detail": {
        "code": "CLIENT_EXISTS",
        "message": "This company already has a client with tax_id 11222333000181.",
        "client_id": CLIENT_ID,
    }
}


class DuplicateTest(unittest.TestCase):
    def test_a_409_duplicate_carries_the_existing_client_id(self):
        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(409, DUPLICATE)

            with self.assertRaises(ClientAlreadyExistsError) as raised:
                _clients().create(name="ACME", tax_id="11222333000181")

        self.assertEqual(raised.exception.client_id, CLIENT_ID)
        self.assertEqual(raised.exception.status_code, 409)
        self.assertIsInstance(raised.exception, APIError)

    def test_an_update_that_takes_another_tax_id_raises_it_too(self):
        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(409, DUPLICATE)

            with self.assertRaises(ClientAlreadyExistsError):
                _clients().update(CLIENT_ID, tax_id="11222333000181")

    def test_another_409_stays_a_plain_api_error(self):
        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(409, {"detail": "conflict"})

            with self.assertRaises(APIError) as raised:
                _clients().create(name="ACME", tax_id="11222333000181")

        self.assertNotIsInstance(raised.exception, ClientAlreadyExistsError)


def _item(**fields):
    return Product(
        description="Teclado", amount=Decimal("10.00"), ncm="84716052", cfop="5102"
    ).model_copy(update=fields)


class IssueWithClientTest(unittest.TestCase):
    def setUp(self):
        self.invoice = Invoice(api_key="k")

    def body(self, **call):
        with patch.object(self.invoice, "_request", return_value={}) as sent:
            self.invoice.issue(**call)
        return sent.call_args.kwargs["json"]

    def test_client_id_alone_names_the_recipient(self):
        body = self.body(
            document_type=DocumentType.NFE, client_id=CLIENT_ID, items=[_item()]
        )

        self.assertEqual(
            json.dumps(body),
            json.dumps(
                {
                    "document_type": "nfe",
                    "client_id": CLIENT_ID,
                    "items": [_item().to_dict()],
                }
            ),
        )

    def test_an_nfse_with_retained_iss_takes_the_clients_address(self):
        body = self.body(
            document_type=DocumentType.NFSE,
            client_id=CLIENT_ID,
            items=[_item(ncm=None, cfop=None, tax_retained=True)],
        )

        self.assertNotIn("recipient_address", body)

    def test_fields_passed_with_client_id_are_sent_to_win(self):
        body = self.body(
            document_type=DocumentType.NFSE,
            client_id=CLIENT_ID,
            client_name="ACME Filial",
            tax_id="11222333000181",
            items=[_item(ncm=None, cfop=None)],
        )

        self.assertEqual(body["client_id"], CLIENT_ID)
        self.assertEqual(body["client_name"], "ACME Filial")
        self.assertEqual(body["tax_id"], "11222333000181")

    def test_a_partial_address_passed_with_client_id_is_still_refused(self):
        with self.assertRaises(ValueError):
            self.body(
                document_type=DocumentType.NFE,
                client_id=CLIENT_ID,
                items=[_item()],
                recipient_address=Address(state="SP"),
            )

    def test_update_client_is_sent_only_when_true(self):
        body = self.body(
            document_type=DocumentType.NFE,
            client_id=CLIENT_ID,
            items=[_item()],
            update_client=True,
        )
        self.assertIs(body["update_client"], True)

        body = self.body(
            document_type=DocumentType.NFE, client_id=CLIENT_ID, items=[_item()]
        )
        self.assertNotIn("update_client", body)

    def test_without_client_id_client_name_is_still_required(self):
        with self.assertRaises(ValueError):
            self.body(
                document_type=DocumentType.NFSE,
                tax_id="11222333000181",
                items=[_item(ncm=None, cfop=None)],
            )

    def test_without_client_id_tax_id_is_still_required(self):
        with self.assertRaises(ValueError):
            self.body(
                document_type=DocumentType.NFSE,
                client_name="ACME",
                items=[_item(ncm=None, cfop=None)],
            )

    def test_without_client_id_the_body_is_what_it_was(self):
        body = self.body(
            document_type=DocumentType.NFSE,
            client_name="ACME",
            tax_id="11222333000181",
            items=[_item(ncm=None, cfop=None)],
        )

        self.assertEqual(
            list(body), ["document_type", "client_name", "tax_id", "items"]
        )


if __name__ == "__main__":
    unittest.main()
