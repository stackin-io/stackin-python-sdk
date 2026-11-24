import unittest
from unittest.mock import patch

from stackin import APIError, Company, DocumentType, Invoice, Items, ValidationResult
from stackin.br import Product
from tests.test_reference import FakeResponse

ACTIVITY = {
    "code": "MEI_ACTIVITY_NOT_ALLOWED",
    "message": "Activity not allowed",
    "field": None,
}


def _invoice():
    return Invoice(base_url="https://sdk.test", api_key="k")


def _issue(client, **extra):
    return client.issue(
        document_type=DocumentType.NFSE,
        client_name="Buyer",
        tax_id="12345678909",
        items=[Product(description="Servico", amount=100, unit_price=100)],
        **extra,
    )


def _sent(call, payload=None, status=200):
    with patch("stackin.core.client.requests.request") as request:
        request.return_value = FakeResponse(status, payload)
        result = call()
    return request.call_args, result


class ProductNbsTest(unittest.TestCase):
    def test_nbs_is_item_level_beside_service_code(self):
        line = Product(
            description="Servico",
            amount=1,
            unit_price=1,
            service_code="01.07",
            nbs="1.1502.10.00",
        ).to_dict()

        self.assertEqual(line["nbs"], "1.1502.10.00")
        self.assertEqual(line["service_code"], "01.07")
        self.assertNotIn("nbs", line["product"])

    def test_nbs_is_omitted_when_unset(self):
        line = Product(description="Servico", amount=1, unit_price=1).to_dict()

        self.assertNotIn("nbs", line)
        self.assertNotIn("nbs", line["product"])

    def test_nbs_reaches_the_issue_body(self):
        (_, kwargs), _ = _sent(
            lambda: _invoice().issue(
                document_type=DocumentType.NFSE,
                client_name="Buyer",
                tax_id="12345678909",
                items=[
                    Product(
                        description="Servico", amount=1, unit_price=1, nbs="115021000"
                    )
                ],
            ),
            {"result": {}},
        )

        self.assertEqual(kwargs["json"]["items"][0]["nbs"], "115021000")


class CatalogNbsTest(unittest.TestCase):
    def _items(self):
        return Items(base_url="https://sdk.test", api_key="k")

    def test_upsert_sends_nbs(self):
        (_, kwargs), _ = _sent(
            lambda: self._items().upsert(
                kind="service", description="Consultoria", nbs="1.1502.10.00"
            ),
            {},
        )

        self.assertEqual(kwargs["json"]["nbs"], "1.1502.10.00")

    def test_create_omits_nbs_when_unset(self):
        (_, kwargs), _ = _sent(
            lambda: self._items().create(kind="service", description="Consultoria"),
            {},
        )

        self.assertNotIn("nbs", kwargs["json"])

    def test_update_sends_nbs_and_can_clear_it(self):
        (_, kwargs), _ = _sent(lambda: self._items().update("i1", nbs="115021000"), {})
        self.assertEqual(kwargs["json"], {"nbs": "115021000"})

        (_, kwargs), _ = _sent(lambda: self._items().update("i1", nbs=None), {})
        self.assertEqual(kwargs["json"], {"nbs": None})

    def test_update_without_nbs_leaves_it_out(self):
        (_, kwargs), _ = _sent(lambda: self._items().update("i1", notes="x"), {})

        self.assertNotIn("nbs", kwargs["json"])


class IssueWarningsTest(unittest.TestCase):
    def test_warnings_are_added_to_the_result(self):
        _, result = _sent(
            lambda: _issue(_invoice()),
            {"result": {"access_key": "abc"}, "warnings": [ACTIVITY]},
        )

        self.assertEqual(result["access_key"], "abc")
        self.assertEqual(result["warnings"], [ACTIVITY])
        self.assertIsNone(result["warnings"][0]["field"])

    def test_warnings_are_empty_when_none(self):
        _, result = _sent(
            lambda: _issue(_invoice()),
            {"result": {"access_key": "abc"}, "warnings": []},
        )

        self.assertEqual(result["warnings"], [])

    def test_warnings_are_empty_when_the_body_has_none(self):
        _, result = _sent(lambda: _issue(_invoice()), {"result": {"access_key": "abc"}})

        self.assertEqual(result["warnings"], [])

    def test_a_bare_body_still_gets_the_key(self):
        _, result = _sent(lambda: _issue(_invoice()), {"access_key": "abc"})

        self.assertEqual(result, {"access_key": "abc", "warnings": []})

    def test_reissue_is_unchanged(self):
        _, result = _sent(
            lambda: _invoice().reissue("inv-1"),
            {"result": {"access_key": "abc"}, "warnings": [ACTIVITY]},
        )

        self.assertEqual(result, {"access_key": "abc"})

    def test_validate_exposes_the_warning_field(self):
        body = {
            "valid": True,
            "warnings": [
                {"code": "ACTIVITY_NOT_REGISTERED", "message": "m", "field": "items[0]"}
            ],
        }
        _, result = _sent(
            lambda: _invoice().validate(
                document_type=DocumentType.NFSE,
                client_name="Buyer",
                tax_id="12345678909",
                items=[Product(description="S", amount=1, unit_price=1)],
            ),
            body,
        )

        self.assertIsInstance(result, ValidationResult)
        self.assertEqual(result.warnings[0].code, "ACTIVITY_NOT_REGISTERED")
        self.assertEqual(result.warnings[0].field, "items[0]")


class AcceptLanguageTest(unittest.TestCase):
    def test_issue_sends_the_header_only(self):
        (_, kwargs), _ = _sent(
            lambda: _issue(_invoice(), accept_language="pt-BR"), {"result": {}}
        )

        self.assertEqual(kwargs["headers"]["Accept-Language"], "pt-BR")
        self.assertNotIn("accept_language", kwargs["json"])
        self.assertNotIn("Accept-Language", str(kwargs["json"]))

    def test_issue_omits_the_header_by_default(self):
        (_, kwargs), _ = _sent(lambda: _issue(_invoice()), {"result": {}})

        self.assertNotIn("Accept-Language", kwargs["headers"])

    def test_validate_sends_the_header_only(self):
        (_, kwargs), _ = _sent(
            lambda: _invoice().validate(
                document_type=DocumentType.NFSE,
                client_name="Buyer",
                tax_id="12345678909",
                items=[Product(description="S", amount=1, unit_price=1)],
                accept_language="es",
            ),
            {"valid": True},
        )

        self.assertEqual(kwargs["headers"]["Accept-Language"], "es")
        self.assertNotIn("accept_language", kwargs["json"])

    def test_validate_omits_the_header_by_default(self):
        (_, kwargs), _ = _sent(
            lambda: _invoice().validate(
                document_type=DocumentType.NFSE,
                client_name="Buyer",
                tax_id="12345678909",
                items=[Product(description="S", amount=1, unit_price=1)],
            ),
            {"valid": True},
        )

        self.assertNotIn("Accept-Language", kwargs["headers"])


class BlockActivityMismatchTest(unittest.TestCase):
    def _company(self):
        return Company(base_url="https://sdk.test", api_key="k")

    def test_true_is_sent(self):
        (_, kwargs), _ = _sent(
            lambda: self._company().update(block_activity_mismatch=True), {}
        )

        self.assertEqual(kwargs["json"], {"block_activity_mismatch": True})

    def test_false_is_sent(self):
        (_, kwargs), _ = _sent(
            lambda: self._company().update(block_activity_mismatch=False), {}
        )

        self.assertEqual(kwargs["json"], {"block_activity_mismatch": False})

    def test_unset_is_left_out(self):
        (_, kwargs), _ = _sent(
            lambda: self._company().update(address={"street": "Rua A"}), {}
        )

        self.assertNotIn("block_activity_mismatch", kwargs["json"])

    def test_a_non_bool_is_refused_before_the_call(self):
        for value in ("true", 1, 0):
            with patch("stackin.core.client.requests.request") as request:
                with self.assertRaises(ValueError):
                    self._company().update(block_activity_mismatch=value)
            request.assert_not_called()

    def test_not_the_owner_is_an_api_error(self):
        with self.assertRaises(APIError) as caught:
            _sent(
                lambda: self._company().update(block_activity_mismatch=True),
                {"detail": "owner only"},
                403,
            )

        self.assertEqual(caught.exception.status_code, 403)
