import unittest
from unittest.mock import patch

import requests

from stackin import (
    Address,
    APIError,
    ConnectionFailedError,
    DocumentType,
    Invoice,
    Manifestation,
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

    def test_cancel_sends_the_header(self):
        """Cancelling is the irreversible one; a blind retry on a dropped
        connection used to reach the authorizer twice."""
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                200, json_data={"result": {"status": "cancelled"}}
            )
            self.client.cancel(
                "42054072268849750000176",
                document_type=DocumentType.NFSE,
                reason="cancelled by the customer",
                idempotency_key="idem-3",
            )

        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs["headers"]["Idempotency-Key"], "idem-3")

    def test_cancel_omits_the_header_by_default(self):
        """Opt-in: only the caller knows which two requests are one."""
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                200, json_data={"result": {"status": "cancelled"}}
            )
            self.client.cancel(
                "42054072268849750000176",
                document_type=DocumentType.NFSE,
                reason="cancelled by the customer",
            )

        _, kwargs = mock_request.call_args
        self.assertNotIn("Idempotency-Key", kwargs["headers"])


class TestClientToleratesUnknownFields(unittest.TestCase):
    """The API may add fields inside v1 — see API_CONTRACT.md §7."""

    def test_an_unknown_field_reaches_the_caller(self):
        client = Invoice(api_key="test-key")

        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                200,
                json_data={
                    "result": {
                        "access_key": "abc",
                        "status": "authorized",
                        "field_invented_next_year": {"nested": [1, 2]},
                    }
                },
            )
            result = client.consult("abc", document_type=DocumentType.NFSE)

        self.assertEqual(result["access_key"], "abc")
        self.assertEqual(
            result["field_invented_next_year"], {"nested": [1, 2]}
        )


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


class TestPdf(unittest.TestCase):
    """The only method that returns bytes rather than a parsed object."""

    def setUp(self):
        self.client = Invoice(api_key="key", base_url="https://api.test")

    def request(self, status_code=200, content=b"%PDF-1.4 fake"):
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                status_code, content=content, text="boom"
            )
            result = self.client.pdf("abc123", document_type=DocumentType.NFSE)
        return result, mock_request

    def test_it_returns_the_bytes_untouched(self):
        result, _ = self.request()

        self.assertEqual(result, b"%PDF-1.4 fake")
        self.assertIsInstance(result, bytes)

    def test_it_gets_the_pdf_path_with_the_document_type(self):
        _, mock_request = self.request()

        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "GET")
        self.assertTrue(args[1].endswith("/invoices/abc123/pdf"))
        self.assertEqual(kwargs["params"], {"document_type": "nfse"})

    def test_the_authorizer_being_down_is_an_api_error(self):
        """502 means the authorizer is unavailable, not a bad invoice."""
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                502, json_data={"detail": "authorizer unavailable"}
            )

            with self.assertRaises(APIError) as caught:
                self.client.pdf("abc123", document_type=DocumentType.NFSE)

        self.assertEqual(caught.exception.status_code, 502)

    def test_nfe_surfaces_the_api_s_501(self):
        """Not a local validation error — the API decides."""
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                501, json_data={"detail": "a PDF isn't available for nfe"}
            )

            with self.assertRaises(APIError) as caught:
                self.client.pdf("abc123", document_type=DocumentType.NFE)

        self.assertEqual(caught.exception.status_code, 501)

    def test_a_network_failure_is_a_connection_error(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.side_effect = requests.ConnectionError("no route")

            with self.assertRaises(ConnectionFailedError):
                self.client.pdf("abc123", document_type=DocumentType.NFSE)


class TestReceived(unittest.TestCase):
    """The recipient's side. Reads what the API already collected — the
    SEFAZ caps how often a CNPJ may ask, so a listing must not call it."""

    def setUp(self):
        self.client = Invoice(api_key="key", base_url="https://api.test")

    def test_it_gets_the_received_list(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                200, json_data={"data": [], "total": 0}
            )
            self.client.received()

        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "GET")
        self.assertTrue(args[1].endswith("/received-invoices"))

    def test_it_passes_pagination_through(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                200, json_data={"data": []}
            )
            self.client.received(limit=10, offset=20)

        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs["params"], {"limit": 10, "offset": 20})

    def test_it_sends_no_empty_pagination(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                200, json_data={"data": []}
            )
            self.client.received()

        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs["params"], {})


class TestManifest(unittest.TestCase):
    def setUp(self):
        self.client = Invoice(api_key="key", base_url="https://api.test")

    def manifest(self, **kwargs):
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                200, json_data={"result": {"status": "registered"}}
            )
            self.client.manifest("abc123", **kwargs)
        return mock_request

    def test_each_answer_reaches_the_manifestation_path(self):
        for manifestation in (
            Manifestation.CONFIRMACAO,
            Manifestation.CIENCIA,
            Manifestation.DESCONHECIMENTO,
        ):
            with self.subTest(manifestation.value):
                mock_request = self.manifest(manifestation=manifestation)

                args, kwargs = mock_request.call_args
                self.assertEqual(args[0], "POST")
                self.assertTrue(
                    args[1].endswith("/received-invoices/abc123/manifestation")
                )
                self.assertEqual(
                    kwargs["json"]["manifestation"], manifestation.value
                )

    def test_operacao_nao_realizada_carries_its_reason(self):
        mock_request = self.manifest(
            manifestation=Manifestation.OPERACAO_NAO_REALIZADA,
            reason="Mercadoria nunca chegou ao endereco",
        )

        _, kwargs = mock_request.call_args
        self.assertEqual(
            kwargs["json"]["reason"], "Mercadoria nunca chegou ao endereco"
        )

    def test_it_is_refused_locally_without_a_reason(self):
        """A fixed rule: no round trip needed to learn it."""
        with self.assertRaises(ValueError):
            self.client.manifest(
                "abc123",
                manifestation=Manifestation.OPERACAO_NAO_REALIZADA,
            )

    def test_a_reason_where_none_is_taken_is_refused_locally(self):
        with self.assertRaises(ValueError):
            self.client.manifest(
                "abc123",
                manifestation=Manifestation.CIENCIA,
                reason="um motivo qualquer aqui",
            )


class TestHistory(unittest.TestCase):
    """The issuer's own side: what this company issued, not what it got."""

    def setUp(self):
        self.client = Invoice(api_key="key", base_url="https://api.test")

    def test_it_gets_the_invoice_list(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                200, json_data={"data": [], "total": 0}
            )
            self.client.history()

        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "GET")
        self.assertTrue(args[1].endswith("/invoices"))
        self.assertEqual(kwargs["params"], {})

    def test_it_sends_the_document_type_as_its_value(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(200, json_data={})
            self.client.history(document_type=DocumentType.NFE)

        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs["params"], {"document_type": "nfe"})

    def test_it_passes_every_filter_through(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(200, json_data={})
            self.client.history(
                status="rejected",
                limit=10,
                offset=20,
                sort_by="created_at",
                order_by="asc",
            )

        _, kwargs = mock_request.call_args
        self.assertEqual(
            kwargs["params"],
            {
                "status": "rejected",
                "limit": 10,
                "offset": 20,
                "sort_by": "created_at",
                "order_by": "asc",
            },
        )

    def test_it_omits_what_the_caller_did_not_ask_for(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(200, json_data={})
            self.client.history(limit=5)

        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs["params"], {"limit": 5})

    def test_it_returns_the_paginated_envelope(self):
        rows = {"data": [{"id": "abc"}], "total": 1, "page": 1}
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(200, json_data=rows)
            result = self.client.history()

        self.assertEqual(result, rows)


class TestSubmissions(unittest.TestCase):
    """consult() says a document was rejected; this says why."""

    def setUp(self):
        self.client = Invoice(api_key="key", base_url="https://api.test")

    def test_it_reads_the_attempts_by_invoice_id(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(200, json_data=[])
            self.client.submissions("abc-123")

        args, _ = mock_request.call_args
        self.assertEqual(args[0], "GET")
        self.assertTrue(args[1].endswith("/invoices/abc-123/submissions"))

    def test_it_returns_what_the_authorizer_answered(self):
        rows = [
            {
                "status": "rejected",
                "status_code": "209",
                "detail": "IE do emitente invalida",
                "raw_response": {"cStat": "209"},
            }
        ]
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(200, json_data=rows)
            result = self.client.submissions("abc-123")

        self.assertEqual(result, rows)


class TestListResponses(unittest.TestCase):
    """A route that answers with a bare list, not the usual envelope."""

    def setUp(self):
        self.client = Invoice(api_key="key", base_url="https://api.test")

    def test_a_list_body_survives_the_envelope_unwrapping(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                200, json_data=[{"id": "one"}, {"id": "two"}]
            )
            result = self.client.submissions("abc-123")

        self.assertEqual(len(result), 2)

    def test_a_dict_body_is_still_unwrapped(self):
        with patch("stackin.core.client.requests.request") as mock_request:
            mock_request.return_value = FakeResponse(
                200, json_data={"result": {"status": "authorized"}}
            )
            result = self.client.consult("key", document_type=DocumentType.NFE)

        self.assertEqual(result, {"status": "authorized"})
