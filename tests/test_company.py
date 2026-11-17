"""Company selection, the companies listing and the refusals they bring."""

import unittest
from unittest.mock import patch

from stackin import (
    APIError,
    CompanyNotInScopeError,
    CompanyRequiredError,
    DocumentType,
    FiscalReference,
    InsufficientPermissionError,
    Invoice,
    Manifestation,
    Taxpayer,
)
from stackin.br import Product
from tests.test_reference import FakeResponse

COMPANY_ID = "6f1c2a9e-1b3d-4c5e-8f70-123456789abc"
TAX_ID = "11.222.333/0001-81"
ACCESS_KEY = "35260112345678000199550010000000011000000012"
LISTING = [
    {
        "company_id": COMPANY_ID,
        "name": "ACME",
        "tax_id": "11222333000181",
        "permissions": ["invoice:read"],
    }
]


def _invoice(**kwargs):
    return Invoice(base_url="https://sdk.test", api_key="k", **kwargs)


def _headers_sent(call, client):
    with patch("stackin.core.client.requests.request") as request:
        request.return_value = FakeResponse(payload={})
        call(client)
    return request.call_args.kwargs["headers"]


class HeaderTest(unittest.TestCase):
    def test_no_company_sends_the_same_headers_as_before(self):
        client = _invoice()
        self.assertEqual(client._headers(), {"Authorization": "Bearer k"})
        self.assertEqual(
            client._headers("idem-1"),
            {"Authorization": "Bearer k", "Idempotency-Key": "idem-1"},
        )

    def test_no_company_sends_the_same_request_as_before(self):
        client = _invoice()

        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(payload={})
            client.consult(ACCESS_KEY, document_type=DocumentType.NFE)

        request.assert_called_once_with(
            "GET",
            f"https://sdk.test/api/v1/invoices/{ACCESS_KEY}",
            json=None,
            params={"document_type": "nfe"},
            headers={"Authorization": "Bearer k"},
            timeout=30,
        )

    def test_the_client_company_is_sent(self):
        headers = _invoice(company=COMPANY_ID)._headers()
        self.assertEqual(headers["X-Stackin-Company"], COMPANY_ID)

    def test_a_cnpj_is_sent_as_given(self):
        headers = _invoice(company=TAX_ID)._headers()
        self.assertEqual(headers["X-Stackin-Company"], TAX_ID)

    def test_an_empty_company_sends_nothing(self):
        self.assertNotIn("X-Stackin-Company", _invoice(company="")._headers())

    def test_a_call_company_wins_over_the_client_company(self):
        client = _invoice(company=COMPANY_ID)
        headers = _headers_sent(
            lambda c: c.history(company=TAX_ID),
            client,
        )
        self.assertEqual(headers["X-Stackin-Company"], TAX_ID)

    def test_a_call_company_works_without_a_client_company(self):
        headers = _headers_sent(lambda c: c.received(company=COMPANY_ID), _invoice())
        self.assertEqual(headers["X-Stackin-Company"], COMPANY_ID)

    def test_a_call_company_does_not_stick_to_the_client(self):
        client = _invoice()
        _headers_sent(lambda c: c.received(company=COMPANY_ID), client)
        headers = _headers_sent(lambda c: c.received(), client)
        self.assertNotIn("X-Stackin-Company", headers)


class EveryRequestTest(unittest.TestCase):
    CALLS = {
        "consult": lambda c, **kw: c.consult(
            ACCESS_KEY, document_type=DocumentType.NFE, **kw
        ),
        "cancel": lambda c, **kw: c.cancel(
            ACCESS_KEY,
            document_type=DocumentType.NFE,
            reason="customer gave up on the order",
            **kw,
        ),
        "invalidate": lambda c, **kw: c.invalidate(
            series="1",
            number_start=1,
            number_end=2,
            reason="numbers skipped by mistake",
            **kw,
        ),
        "correct": lambda c, **kw: c.correct(
            ACCESS_KEY,
            document_type=DocumentType.NFE,
            correction="the street name was misspelled",
            **kw,
        ),
        "reissue": lambda c, **kw: c.reissue("inv-1", **kw),
        "pdf": lambda c, **kw: c.pdf(ACCESS_KEY, document_type=DocumentType.NFSE, **kw),
        "received": lambda c, **kw: c.received(**kw),
        "history": lambda c, **kw: c.history(**kw),
        "submissions": lambda c, **kw: c.submissions("inv-1", **kw),
        "manifest": lambda c, **kw: c.manifest(
            ACCESS_KEY, manifestation=Manifestation.CIENCIA, **kw
        ),
        "companies": lambda c, **kw: c.companies(**kw),
    }

    def test_every_invoice_request_carries_the_client_company(self):
        for name, call in self.CALLS.items():
            with self.subTest(method=name):
                headers = _headers_sent(call, _invoice(company=COMPANY_ID))
                self.assertEqual(headers["X-Stackin-Company"], COMPANY_ID)

    def test_every_invoice_request_without_company_has_no_header(self):
        for name, call in self.CALLS.items():
            with self.subTest(method=name):
                headers = _headers_sent(call, _invoice())
                self.assertNotIn("X-Stackin-Company", headers)

    def test_every_invoice_method_but_companies_takes_a_call_company(self):
        for name, call in self.CALLS.items():
            if name == "companies":
                continue
            with self.subTest(method=name):
                headers = _headers_sent(
                    lambda c, call=call: call(c, company=TAX_ID), _invoice()
                )
                self.assertEqual(headers["X-Stackin-Company"], TAX_ID)

    def test_issue_carries_the_call_company(self):
        headers = _headers_sent(
            lambda c: c.issue(
                document_type=DocumentType.NFSE,
                client_name="Buyer",
                tax_id="11222333000181",
                items=[Product(description="Service", amount=10.0)],
                company=COMPANY_ID,
            ),
            _invoice(),
        )
        self.assertEqual(headers["X-Stackin-Company"], COMPANY_ID)

    def test_a_taxpayer_lookup_carries_the_client_company(self):
        client = Taxpayer(base_url="https://sdk.test", api_key="k", company=TAX_ID)
        headers = _headers_sent(lambda c: c.get("11222333000181"), client)
        self.assertEqual(headers["X-Stackin-Company"], TAX_ID)

    def test_a_fiscal_reference_lookup_carries_the_client_company(self):
        client = FiscalReference(
            base_url="https://sdk.test", api_key="k", company=COMPANY_ID
        )
        headers = _headers_sent(lambda c: c.ncm.get("01012100"), client)
        self.assertEqual(headers["X-Stackin-Company"], COMPANY_ID)

    def test_a_lookup_without_company_has_no_header(self):
        client = Taxpayer(base_url="https://sdk.test", api_key="k")
        headers = _headers_sent(lambda c: c.get("11222333000181"), client)
        self.assertEqual(headers, {"Authorization": "Bearer k"})


class CompaniesTest(unittest.TestCase):
    def test_it_lists_the_companies_the_credential_covers(self):
        payload = {"environment": "production", "companies": LISTING}

        with patch("stackin.core.client.requests.request") as request:
            request.return_value = FakeResponse(payload=payload)
            result = _invoice().companies()

        args, kwargs = request.call_args
        self.assertEqual(args[0], "GET")
        self.assertEqual(args[1], "https://sdk.test/api/v1/me/companies")
        self.assertIsNone(kwargs["json"])
        self.assertIsNone(kwargs["params"])
        self.assertEqual(result, payload)


def _refused(status_code, detail):
    client = _invoice()
    with patch("stackin.core.client.requests.request") as request:
        request.return_value = FakeResponse(status_code, {"detail": detail})
        try:
            client.history()
        except APIError as error:
            return error, request.call_count
    raise AssertionError("no error raised")


class RefusalTest(unittest.TestCase):
    def test_company_required_is_typed_and_lists_the_companies(self):
        detail = {
            "error": "company_required",
            "error_description": "This credential covers several companies.",
            "companies": LISTING,
        }
        error, calls = _refused(422, detail)

        self.assertIsInstance(error, CompanyRequiredError)
        self.assertIsInstance(error, APIError)
        self.assertEqual(error.status_code, 422)
        self.assertEqual(error.detail, detail)
        self.assertEqual(error.companies, LISTING)
        self.assertEqual(calls, 1)

    def test_company_not_in_scope_is_typed_and_lists_the_companies(self):
        detail = {
            "error": "company_not_in_scope",
            "error_description": "This credential does not cover company x.",
            "companies": LISTING,
        }
        error, calls = _refused(403, detail)

        self.assertIsInstance(error, CompanyNotInScopeError)
        self.assertEqual(error.status_code, 403)
        self.assertEqual(error.companies, LISTING)
        self.assertEqual(calls, 1)

    def test_insufficient_permission_is_typed_and_carries_the_description(self):
        description = (
            "INSUFFICIENT_PERMISSION: needs invoice:issue, has invoice:read, "
            f"company={COMPANY_ID}"
        )
        detail = {
            "error": "insufficient_scope",
            "error_description": description,
            "code": "INSUFFICIENT_PERMISSION",
        }
        error, calls = _refused(403, detail)

        self.assertIsInstance(error, InsufficientPermissionError)
        self.assertEqual(error.status_code, 403)
        self.assertEqual(error.description, description)
        self.assertEqual(calls, 1)

    def test_a_missing_companies_list_is_empty(self):
        error, _ = _refused(422, {"error": "company_required"})
        self.assertIsInstance(error, CompanyRequiredError)
        self.assertEqual(error.companies, [])

    def test_another_403_stays_a_plain_api_error(self):
        error, _ = _refused(403, "Forbidden")
        self.assertIs(type(error), APIError)
        self.assertEqual(error.detail, "Forbidden")

    def test_another_422_stays_a_plain_api_error(self):
        detail = [{"loc": ["body", "items"], "msg": "field required"}]
        error, _ = _refused(422, detail)
        self.assertIs(type(error), APIError)
        self.assertEqual(error.detail, detail)

    def test_the_error_code_on_the_wrong_status_stays_a_plain_api_error(self):
        error, _ = _refused(400, {"error": "company_required"})
        self.assertIs(type(error), APIError)


if __name__ == "__main__":
    unittest.main()
