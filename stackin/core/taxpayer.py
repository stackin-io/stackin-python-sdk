"""The taxpayer registry, looked up one tax id at a time.

One method, and it stays one method. The registry names and addresses
real people and companies: an exact lookup answers the question an
issuer has — who is this CNPJ I am about to invoice — and answers
nothing else. A prefix or wildcard search over the same table is a bulk
export wearing the costume of a query. Do not add one, not for parity
with FiscalReference, not "just by name", not "just within one state".
"""

from __future__ import annotations

from typing import cast

from stackin.core.client import _Client
from stackin.core.reference import _segment
from stackin.core.types import Environment


class Taxpayer(_Client):
    """Client for the taxpayer registry."""

    def __init__(
        self,
        base_url: str | None = None,
        environment: Environment | str | None = None,
        api_key: str | None = None,
        timeout: int = 30,
        country: str = "BR",
    ) -> None:
        super().__init__(base_url, environment, api_key, timeout)
        self.country = country

    def get(self, tax_id: str, *, country: str | None = None) -> dict:
        """One taxpayer, by exact tax id.

        A 404 raises APIError and does not mean the taxpayer does not
        exist: the registry reloads monthly, so a company registered in
        the last few weeks is simply not in it yet. Never build a
        validation rule on top of it.
        """
        return cast(
            dict,
            self._request(
                "GET",
                f"/taxpayers/{_segment(tax_id)}",
                params={"country": country or self.country},
            ),
        )
