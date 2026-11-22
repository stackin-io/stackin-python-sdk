"""FiscalReference.calculate_ibs_cbs: the body it sends and the result it reads."""

import unittest
from datetime import date
from typing import Any
from unittest.mock import patch

from pydantic import ValidationError

from stackin import (
    APIError,
    FiscalReference,
    IbsCbsCalculation,
    IbsCbsCalculationItem,
    IbsCbsRates,
)
from tests.test_reference import FakeResponse

AMOUNTS = {
    "base": "100.00",
    "ibs_state": "0.10",
    "ibs_city": "0.00",
    "ibs": "0.10",
    "cbs": "0.90",
    "deferred_ibs_state": "0.00",
    "deferred_ibs_city": "0.00",
    "deferred_cbs": "0.00",
}

ANSWER: dict[str, Any] = {
    "simulated": True,
    "notice": "Simulation only: not a fiscal document and no legal effect.",
    "document_type": "nfe",
    "operation_date": "2026-11-22",
    "items": [
        {
            "cst": "000",
            "classification": "000001",
            "indicators": {"group": 1, "reduction": 0, "deferral": 0},
            "has_group": True,
            "rates": {
                "rate_state": "0.1000",
                "rate_city": "0.0000",
                "rate_federal": "0.9000",
            },
            "rates_source": "official_2026",
            "reduction_ibs": None,
            "reduction_cbs": None,
            "effective_rates": None,
            "deferral": None,
            "amounts": AMOUNTS,
            "added_later": "ignored",
        }
    ],
    "total": AMOUNTS,
}


def _sent(call, status=200, payload=None):
    client = FiscalReference(base_url="https://sdk.test", api_key="k")
    with patch("stackin.core.client.requests.request") as request:
        request.return_value = FakeResponse(
            status, payload if payload is not None else ANSWER
        )
        result = call(client)
    return request.call_args, result


class CalculateTest(unittest.TestCase):
    def test_it_posts_only_what_is_set(self):
        (args, kwargs), _ = _sent(
            lambda c: c.calculate_ibs_cbs(
                [{"cst": "000", "classification": "000001", "amount": 100}],
                operation_date="2026-11-22",
            )
        )

        self.assertEqual(
            args[:2], ("POST", "https://sdk.test/api/v1/ibs-cbs/calculate")
        )
        self.assertEqual(
            kwargs["json"],
            {
                "document_type": "nfe",
                "operation_date": "2026-11-22",
                "items": [{"cst": "000", "classification": "000001", "amount": 100}],
            },
        )

    def test_rates_models_and_dates_are_accepted(self):
        (_, kwargs), _ = _sent(
            lambda c: c.calculate_ibs_cbs(
                [
                    IbsCbsCalculationItem(
                        cst="200",
                        classification="200003",
                        base=50,
                        rate_city=0,
                        reduction_ibs=60,
                    )
                ],
                operation_date=date(2027, 1, 5),
                document_type="nfse",
                rates=IbsCbsRates(rate_state=0.1, rate_city=0, rate_federal=0.9),
            )
        )

        self.assertEqual(
            kwargs["json"],
            {
                "document_type": "nfse",
                "operation_date": "2027-01-05",
                "items": [
                    {
                        "cst": "200",
                        "classification": "200003",
                        "base": 50,
                        "rate_city": 0,
                        "reduction_ibs": 60,
                    }
                ],
                "rates": {"rate_state": 0.1, "rate_city": 0, "rate_federal": 0.9},
            },
        )

    def test_empty_rates_are_not_sent(self):
        (_, kwargs), _ = _sent(
            lambda c: c.calculate_ibs_cbs(
                [{"cst": "000", "classification": "000001", "amount": 1}],
                operation_date="2026-01-01",
                rates={},
            )
        )

        self.assertNotIn("rates", kwargs["json"])

    def test_the_answer_is_typed(self):
        _, result = _sent(
            lambda c: c.calculate_ibs_cbs(
                [{"cst": "000", "classification": "000001", "amount": 100}],
                operation_date="2026-11-22",
            )
        )

        self.assertIsInstance(result, IbsCbsCalculation)
        self.assertTrue(result.simulated)
        self.assertEqual(result.operation_date, date(2026, 11, 22))
        self.assertEqual(result.items[0].rates_source, "official_2026")
        self.assertEqual(result.items[0].rates.rate_federal, "0.9000")
        self.assertEqual(result.items[0].indicators.group, 1)
        self.assertEqual(result.total.cbs, "0.90")

    def test_a_refusal_is_an_api_error(self):
        refusal = {"code": "IBS_CBS_RATES_REQUIRED", "message": "rates required"}
        with self.assertRaises(APIError) as caught:
            _sent(
                lambda c: c.calculate_ibs_cbs(
                    [{"cst": "000", "classification": "000001", "amount": 1}],
                    operation_date="2027-01-01",
                ),
                status=422,
                payload=refusal,
            )

        self.assertEqual(caught.exception.status_code, 422)

    def test_refusals_before_the_call(self):
        item = {"cst": "000", "classification": "000001", "amount": 1}
        cases: dict[str, dict[str, Any]] = {
            "no items": {"items": []},
            "too many items": {"items": [item] * 991},
            "short cst": {"items": [{**item, "cst": "00"}]},
            "short classification": {"items": [{**item, "classification": "1"}]},
            "no amount nor base": {"items": [{"cst": "000", "classification": "1"}]},
            "zero amount": {"items": [{**item, "amount": 0}]},
            "rate above 100": {"items": [{**item, "rate_state": 101}]},
            "unknown item field": {"items": [{**item, "operation_indicator": "1"}]},
            "unknown rate": {"items": [item], "rates": {"rate": 1}},
            "bad date": {"items": [item], "operation_date": "22/11/2026"},
            "bad document type": {"items": [item], "document_type": "cte"},
        }
        for message, given in cases.items():
            kwargs: dict[str, Any] = {"operation_date": "2026-11-22", **given}
            items = kwargs.pop("items")
            with self.subTest(message):
                with patch("stackin.core.client.requests.request") as request:
                    with self.assertRaises((ValueError, ValidationError)):
                        FiscalReference(
                            base_url="https://sdk.test", api_key="k"
                        ).calculate_ibs_cbs(items, **kwargs)
                    request.assert_not_called()
