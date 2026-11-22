"""The published classification tables — CFOP, NCM, CEST and the rest.

None of this is the company's own data and none of it is writable. The
eight named accessors are ergonomics; `kind()` is the contract, and it
reaches a classification published after this release without one.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any, Literal, cast
from urllib.parse import quote

from stackin.core.client import _Client
from stackin.core.ibs_cbs import IbsCbsCalculation, IbsCbsCalculationItem, IbsCbsRates
from stackin.core.types import Environment


def _segment(value: str) -> str:
    """One path segment, escaped, refusing what would leave it.

    `safe=""` because a code the caller typed may hold a `/`. The dot
    segments need refusing rather than escaping: RFC 3986 calls `.`
    unreserved, so `quote` leaves it alone and the HTTP client then
    collapses `..` into a different endpoint.
    """
    if value in ("", ".", ".."):
        raise ValueError(f"{value!r} is not a usable path segment")
    return quote(value, safe="")


KINDS = (
    "cfop",
    "ncm",
    "cest",
    "cst",
    "csosn",
    "iss_service",
    "icms_fuel",
    "ibs_cbs_class",
)


class Kind:
    """One classification, bound to a country."""

    def __init__(self, client: _Client, name: str, country: str) -> None:
        self._client = client
        self.name = name
        self.country = country

    def get(self, code: str, *, country: str | None = None) -> dict:
        """One code. A code that does not exist raises APIError (404)."""
        return cast(
            dict,
            self._client._request(
                "GET",
                f"/fiscal-references/{_segment(self.name)}" f"/{_segment(code)}",
                params={"country": country or self.country},
            ),
        )

    def search(
        self,
        term: str | None = None,
        *,
        country: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict:
        """This classification, searched or simply paged through.

        Rows come back ordered by kind then code; the API takes no
        sort_by or order_by here, unlike Invoice.history().
        """
        return _search(
            self._client,
            country=country or self.country,
            kind=self.name,
            term=term,
            limit=limit,
            offset=offset,
        )


def _search(
    client: _Client,
    *,
    country: str,
    kind: str | None,
    term: str | None,
    limit: int | None,
    offset: int | None,
) -> dict:
    """Shared by Kind.search and FiscalReference.search."""
    params: dict[str, Any] = {"country": country}
    if kind is not None:
        params["kind"] = kind
    if term:
        params["search"] = term
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset

    return cast(
        dict,
        client._request("GET", "/fiscal-references", params=params),
    )


class FiscalReference(_Client):
    """Client for the published fiscal classification tables."""

    def __init__(
        self,
        base_url: str | None = None,
        environment: Environment | str | None = None,
        api_key: str | None = None,
        timeout: int = 30,
        country: str = "BR",
        company: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(base_url, environment, api_key, timeout, company, headers)
        self.country = country

        self.cfop = Kind(self, "cfop", country)
        self.ncm = Kind(self, "ncm", country)
        self.cest = Kind(self, "cest", country)
        self.cst = Kind(self, "cst", country)
        self.csosn = Kind(self, "csosn", country)
        self.iss_service = Kind(self, "iss_service", country)
        self.icms_fuel = Kind(self, "icms_fuel", country)
        self.ibs_cbs_class = Kind(self, "ibs_cbs_class", country)

    def kinds(self, *, country: str | None = None) -> list[str]:
        """Which classifications this country has data for.

        The only honest answer to "what else is there" — a hard-coded
        list in a README goes stale the next time the ETL grows one.
        """
        return cast(
            list[str],
            self._request(
                "GET",
                "/fiscal-references/kinds",
                params={"country": country or self.country},
            ),
        )

    def kind(self, name: str, *, country: str | None = None) -> Kind:
        """Any classification by name, including one with no accessor."""
        return Kind(self, name, country or self.country)

    def search(
        self,
        term: str | None = None,
        *,
        country: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict:
        """Every classification at once, which no accessor can express.

        The most expensive call the endpoint accepts: it is the whole
        country's tables, not one of them.
        """
        return _search(
            self,
            country=country or self.country,
            kind=None,
            term=term,
            limit=limit,
            offset=offset,
        )

    def cities(
        self,
        name: str,
        *,
        state: str | None = None,
        country: str | None = None,
    ) -> list[dict]:
        """Municipalities whose name starts with `name`, with their code.

        Each row is `{country, code, name, state}`; for Brazil `code` is
        the 7-digit IBGE code an address's `city_code` takes. Issuing
        resolves it from city and state by itself, so this is for the
        name that matches more than one. `state` narrows to one UF; the
        API answers at most 20 rows.
        """
        if not 2 <= len(name) <= 100:
            raise ValueError("name must be 2 to 100 characters")
        if state is not None and len(state) != 2:
            raise ValueError("state must be a two-letter code")

        params: dict[str, Any] = {
            "name": name,
            "country": country or self.country,
        }
        if state is not None:
            params["state"] = state.upper()

        return cast(list[dict], self._request("GET", "/cities", params=params))

    def calculate_ibs_cbs(
        self,
        items: Sequence[IbsCbsCalculationItem | Mapping[str, Any]],
        *,
        operation_date: date | str,
        document_type: Literal["nfe", "nfce", "nfse"] = "nfe",
        rates: IbsCbsRates | Mapping[str, Any] | None = None,
        company: str | None = None,
    ) -> IbsCbsCalculation:
        """Simulates the NF-e IBS/CBS group of 1 to 990 items.

        Nothing is issued, stored or sent to a tax authority, and the
        result is not a fiscal document. `document_type` only picks the
        model the cClassTrib is checked for: the amounts are always the
        NF-e's, since an NFS-e's are computed by the Sefin Nacional.
        `rates` apply to every item, and an item's own rate wins. With
        no rates and an `operation_date` in 2026 the official 2026
        rates apply; outside 2026 they are required, or the API answers
        APIError 422 IBS_CBS_RATES_REQUIRED.
        """
        if document_type not in ("nfe", "nfce", "nfse"):
            raise ValueError("document_type must be nfe, nfce or nfse")
        if not 1 <= len(items) <= 990:
            raise ValueError("items must hold 1 to 990 items")
        if isinstance(operation_date, str):
            operation_date = date.fromisoformat(operation_date)

        payload: dict[str, Any] = {
            "document_type": document_type,
            "operation_date": operation_date.isoformat(),
            "items": [
                IbsCbsCalculationItem.model_validate(item).model_dump(exclude_none=True)
                for item in items
            ],
        }
        if rates is not None:
            given = IbsCbsRates.model_validate(rates).model_dump(exclude_none=True)
            if given:
                payload["rates"] = given

        return IbsCbsCalculation.model_validate(
            self._request("POST", "/ibs-cbs/calculate", json=payload, company=company)
        )
