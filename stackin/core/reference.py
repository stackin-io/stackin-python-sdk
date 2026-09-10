"""The published classification tables — CFOP, NCM, CEST and the rest.

None of this is the company's own data and none of it is writable. The
eight named accessors are ergonomics; `kind()` is the contract, and it
reaches a classification published after this release without one.
"""

from __future__ import annotations

from typing import Any, cast

from stackin.core.client import _Client

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
                f"/fiscal-references/{self.name}/{code}",
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

    def __init__(self, *args: Any, country: str = "BR", **kwargs: Any):
        super().__init__(*args, **kwargs)
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
