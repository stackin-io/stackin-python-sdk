import unittest
from unittest.mock import patch

import requests

from stackin import (
    Address,
    APIError,
    ConnectionFailedError,
    DocumentType,
    Invoice,
)
from stackin.br import Product


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, text="", content=b"x"):
        self.status_code = status_code
        self.ok = 200 <= status_code < 300
        self._json_data = json_data
        self.text = text
        self.content = content

    def json(self):
        if self._json_data is None:
            raise ValueError("no json")
        return self._json_data


class TestClientBaseUrlResolution(unittest.TestCase):
    def test_defaults_to_sdk_host(self):
        client = Invoice(api_key="test-key")
        self.assertEqual(client.base_url, "https://sdk.stackin.io")

    def test_uses_explicit_base_url(self):
        client = Invoice(base_url="http://localhost:8000", api_key="test-key")
        self.assertEqual(client.base_url, "http://localhost:8000")

    def test_strips_trailing_slash_from_base_url(self):
        client = Invoice(base_url="http://localhost:8000/", api_key="test-key")
        self.assertEqual(client.base_url, "http://localhost:8000")

    def test_uses_environment_param(self):
        client = Invoice(environment="local", api_key="test-key")
        self.assertEqual(client.base_url, "http://localhost:8000")

    def test_uses_stackin_base_url_env_var(self):
        with patch.dict(
            "os.environ",
            {"STACKIN_BASE_URL": "http://env-url:9000"},
            clear=True,
        ):
            client = Invoice(api_key="test-key")
        self.assertEqual(client.base_url, "http://env-url:9000")

    def test_base_url_env_var_wins_over_environment_param(self):
        with patch.dict(
            "os.environ",
            {"STACKIN_BASE_URL": "http://env-url:9000"},
            clear=True,
        ):
            client = Invoice(environment="local", api_key="test-key")
        self.assertEqual(client.base_url, "http://env-url:9000")

    def test_uses_stackin_environment_env_var(self):
        with patch.dict(
            "os.environ", {"STACKIN_ENVIRONMENT": "local"}, clear=True
        ):
            client = Invoice(api_key="test-key")
        self.assertEqual(client.base_url, "http://localhost:8000")

    def test_explicit_base_url_wins_over_everything(self):
        with patch.dict(
            "os.environ",
            {"STACKIN_BASE_URL": "http://env-url:9000"},
            clear=True,
        ):
            client = Invoice(
                base_url="http://explicit:1234", api_key="test-key"
            )
        self.assertEqual(client.base_url, "http://explicit:1234")

    def test_reads_api_key_from_env_var(self):
        with patch.dict(
            "os.environ", {"STACKIN_API_KEY": "env-key"}, clear=True
        ):
            client = Invoice()
        self.assertEqual(client.api_key, "env-key")


class TestClientHeaders(unittest.TestCase):
    def test_include_bearer_token_when_api_key_set(self):
        client = Invoice(api_key="test-key")
        self.assertEqual(
            client._headers(), {"Authorization": "Bearer test-key"}
        )

    def test_empty_without_api_key(self):
        client = Invoice(api_key=None)
        self.assertEqual(client._headers(), {})

    def test_include_idempotency_key_when_given(self):
        client = Invoice(api_key="test-key")
        self.assertEqual(
            client._headers("idem-1"),
            {
                "Authorization": "Bearer test-key",
                "Idempotency-Key": "idem-1",
            },
        )

    def test_omit_idempotency_key_when_not_given(self):
        client = Invoice(api_key="test-key")
        self.assertNotIn("Idempotency-Key", client._headers())


class TestClientIssueValidation(unittest.TestCase):
    def setUp(self):
        self.client = Invoice(api_key="test-key")

    def test_raises_on_empty_items(self):
        with self.assertRaisesRegex(ValueError, "items can't be empty"):
            self.client.issue(
                document_type=DocumentType.NFSE,
                client_name="Buyer",
                tax_id="123",
                items=[],
            )

    def test_requires_ncm_for_nfe(self):
        item = Product(description="Produto", amount=10.0, cfop="5102")
        with self.assertRaisesRegex(
            ValueError, r"items\[0\].ncm is required for NFE"
        ):
            self.client.issue(
                document_type=DocumentType.NFE,
                client_name="Buyer",
                tax_id="123",
                items=[item],
            )

    def test_requires_cfop_for_nfe(self):
        item = Product(description="Produto", amount=10.0, ncm="12345678")
        with self.assertRaisesRegex(
            ValueError, r"items\[0\].cfop is required for NFE"
        ):
            self.client.issue(
                document_type=DocumentType.NFE,
                client_name="Buyer",
                tax_id="123",
                items=[item],
            )

    def test_requires_recipient_address_for_nfe(self):
        item = Product(
            description="Produto", amount=10.0, ncm="12345678", cfop="5102"
        )
        with self.assertRaisesRegex(
            ValueError, "recipient_address is required for NFE"
        ):
            self.client.issue(
                document_type=DocumentType.NFE,
                client_name="Buyer",
                tax_id="123",
                items=[item],
            )

    def test_rejects_partial_recipient_address_for_nfe(self):
        item = Product(
            description="Produto", amount=10.0, ncm="12345678", cfop="5102"
        )
        with self.assertRaisesRegex(ValueError, "city_code"):
            self.client.issue(
                document_type=DocumentType.NFE,
                client_name="Buyer",
                tax_id="123",
                items=[item],
                recipient_address=Address(state="SC"),
            )


class TestClientIssue(unittest.TestCase):
    def setUp(self):
        self.client = Invoice(api_key="test-key")

    def test_builds_correct_payload_and_returns_result(self):
        item = Product(description="Servico", amount=100.0)

        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                200, json_data={"result": {"access_key": "abc"}}
            )
            result = self.client.issue(
                document_type=DocumentType.NFSE,
                client_name="Buyer",
                tax_id="123",
                items=[item],
            )

        self.assertEqual(result, {"access_key": "abc"})
        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs["json"]["document_type"], "nfse")
        self.assertEqual(kwargs["json"]["client_name"], "Buyer")
        self.assertEqual(kwargs["json"]["tax_id"], "123")
        self.assertNotIn("recipient_address", kwargs["json"])
        self.assertNotIn("series", kwargs["json"])
        self.assertNotIn("number", kwargs["json"])

    def test_includes_recipient_address_series_and_number(self):
        item = Product(description="Servico", amount=100.0)
        address = Address(state="SP")

        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                200, json_data={"result": {}}
            )
            self.client.issue(
                document_type=DocumentType.NFSE,
                client_name="Buyer",
                tax_id="123",
                items=[item],
                recipient_address=address,
                series="1",
                number="42",
            )

        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs["json"]["recipient_address"], {"state": "SP"})
        self.assertEqual(kwargs["json"]["series"], "1")
        self.assertEqual(kwargs["json"]["number"], "42")


class TestClientConsultAndCancel(unittest.TestCase):
    def setUp(self):
        self.client = Invoice(api_key="test-key")

    def test_consult_sends_get_with_document_type_param(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                200, json_data={"result": {}}
            )
            self.client.consult("abc123", document_type=DocumentType.NFE)

        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "GET")
        self.assertTrue(args[1].endswith("/invoices/abc123"))
        self.assertEqual(kwargs["params"], {"document_type": "nfe"})

    def test_cancel_sends_post_with_reason(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                200, json_data={"result": {}}
            )
            self.client.cancel(
                "abc123", document_type=DocumentType.NFE, reason="duplicate"
            )

        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "POST")
        self.assertTrue(args[1].endswith("/invoices/abc123/cancel"))
        self.assertEqual(
            kwargs["json"], {"document_type": "nfe", "reason": "duplicate"}
        )

    def test_reissue_sends_post_to_reissue_path(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                200, json_data={"access_key": "reissued-key"}
            )
            result = self.client.reissue("inv-1")

        args, _kwargs = mock_request.call_args
        self.assertEqual(args[0], "POST")
        self.assertTrue(args[1].endswith("/invoices/inv-1/reissue"))
        self.assertEqual(result, {"access_key": "reissued-key"})


class TestClientInvalidate(unittest.TestCase):
    def setUp(self):
        self.client = Invoice(api_key="test-key")
        self.reason = "Numeracao reservada e nao utilizada por falha no ERP"

    def test_posts_to_the_invalidations_path(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                200, json_data={"id": "range-1", "status": "invalidated"}
            )
            result = self.client.invalidate(
                series="1",
                number_start=10,
                number_end=12,
                reason=self.reason,
            )

        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "POST")
        self.assertTrue(args[1].endswith("/invoices/invalidations"))
        self.assertEqual(
            kwargs["json"],
            {
                "series": "1",
                "number_start": 10,
                "number_end": 12,
                "reason": self.reason,
            },
        )
        self.assertEqual(result["status"], "invalidated")

    def test_rejects_a_reason_under_15_characters(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            with self.assertRaises(ValueError):
                self.client.invalidate(
                    series="1",
                    number_start=10,
                    number_end=12,
                    reason="curto",
                )
            mock_request.assert_not_called()

    def test_rejects_a_reason_over_255_characters(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            with self.assertRaises(ValueError):
                self.client.invalidate(
                    series="1",
                    number_start=10,
                    number_end=12,
                    reason="a" * 256,
                )
            mock_request.assert_not_called()

    def test_rejects_a_backwards_range(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            with self.assertRaises(ValueError):
                self.client.invalidate(
                    series="1",
                    number_start=12,
                    number_end=10,
                    reason=self.reason,
                )
            mock_request.assert_not_called()


class TestClientCorrect(unittest.TestCase):
    def setUp(self):
        self.client = Invoice(api_key="test-key")
        self.text = "Transportadora corrigida para Rapido Ltda"

    def test_posts_to_the_correction_path(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                200, json_data={"result": {"status": "authorized"}}
            )
            result = self.client.correct(
                "abc123",
                document_type=DocumentType.NFE,
                correction=self.text,
            )

        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "POST")
        self.assertTrue(args[1].endswith("/invoices/abc123/correction"))
        self.assertEqual(
            kwargs["json"],
            {"document_type": "nfe", "correction": self.text},
        )
        self.assertEqual(result, {"status": "authorized"})

    def test_rejects_a_correction_under_15_characters(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            with self.assertRaises(ValueError):
                self.client.correct(
                    "abc123",
                    document_type=DocumentType.NFE,
                    correction="curto demais",
                )
            mock_request.assert_not_called()

    def test_rejects_a_correction_over_1000_characters(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            with self.assertRaises(ValueError):
                self.client.correct(
                    "abc123",
                    document_type=DocumentType.NFE,
                    correction="a" * 1001,
                )
            mock_request.assert_not_called()


class TestClientIdempotency(unittest.TestCase):
    def setUp(self):
        self.client = Invoice(api_key="test-key")

    def test_issue_sends_the_header(self):
        item = Product(description="Servico", amount=100.0)

        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                200, json_data={"result": {"access_key": "abc"}}
            )
            self.client.issue(
                document_type=DocumentType.NFSE,
                client_name="Buyer",
                tax_id="123",
                items=[item],
                idempotency_key="idem-1",
            )

        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs["headers"]["Idempotency-Key"], "idem-1")

    def test_issue_omits_the_header_by_default(self):
        item = Product(description="Servico", amount=100.0)

        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                200, json_data={"result": {"access_key": "abc"}}
            )
            self.client.issue(
                document_type=DocumentType.NFSE,
                client_name="Buyer",
                tax_id="123",
                items=[item],
            )

        _, kwargs = mock_request.call_args
        self.assertNotIn("Idempotency-Key", kwargs["headers"])

    def test_reissue_sends_the_header(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                200, json_data={"access_key": "reissued-key"}
            )
            self.client.reissue("inv-1", idempotency_key="idem-2")

        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs["headers"]["Idempotency-Key"], "idem-2")


class TestClientRequestHandling(unittest.TestCase):
    def setUp(self):
        self.client = Invoice(api_key="test-key")

    def test_returns_full_body_when_no_result_key(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                200, json_data={"status": "ok"}
            )
            result = self.client.consult("abc", document_type=DocumentType.NFE)
        self.assertEqual(result, {"status": "ok"})

    def test_handles_empty_response_body(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(200, content=b"")
            result = self.client.consult("abc", document_type=DocumentType.NFE)
        self.assertEqual(result, {})

    def test_handles_non_json_response_body(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                200, json_data=None, content=b"x"
            )
            result = self.client.consult("abc", document_type=DocumentType.NFE)
        self.assertEqual(result, {})

    def test_raises_connection_failed_error_on_request_exception(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.side_effect = requests.ConnectionError("boom")
            with self.assertRaises(ConnectionFailedError):
                self.client.consult("abc", document_type=DocumentType.NFE)

    def test_raises_api_error_with_detail_from_body(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                400, json_data={"detail": "bad request"}
            )
            with self.assertRaises(APIError) as ctx:
                self.client.consult("abc", document_type=DocumentType.NFE)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception.detail, "bad request")

    def test_raises_api_error_falling_back_to_response_text(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                500, json_data=None, text="internal error", content=b"x"
            )
            with self.assertRaises(APIError) as ctx:
                self.client.consult("abc", document_type=DocumentType.NFE)
        self.assertEqual(ctx.exception.status_code, 500)
        self.assertEqual(ctx.exception.detail, "internal error")


if __name__ == "__main__":
    unittest.main()
