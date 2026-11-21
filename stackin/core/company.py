"""The issuer itself: `PATCH /company`.

Fixes what `Invoice.readiness()` reports missing — the address and, for
the company owner, the fiscal fields — and answers whether the company
can issue now. Reading stays `Invoice.readiness()`; this type only
writes.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any, cast

from stackin.core.client import _Client

ADDRESS_FIELDS = (
    "street",
    "number",
    "neighborhood",
    "municipality_code",
    "municipality_name",
    "zip_code",
)

FISCAL_FIELDS = (
    "tax_regime",
    "simples_nacional",
    "simples_apuracao",
    "state_registration",
    "service_code",
)

_ENUMS = {
    "tax_regime": ("1", "2", "3", "4"),
    "simples_nacional": ("1", "2", "3"),
    "simples_apuracao": ("1", "2", "3"),
}


class Company(_Client):
    """Client for the issuer's own address and fiscal fields."""

    def update(
        self,
        *,
        address: Mapping[str, str | None] | None = None,
        fiscal_fields: Mapping[str, str | None] | None = None,
        company: str | None = None,
    ) -> dict:
        """Fixes the issuer's address and, for the owner, its fiscal fields.

        `address` takes street, number, neighborhood, municipality_code
        (7-digit IBGE code of a city in the company's state),
        municipality_name and zip_code (8-digit CEP, a mask accepted).
        There is no complement, and the state changes only in the
        dashboard. `fiscal_fields` takes tax_regime (CRT 1-4),
        simples_nacional (1-3), simples_apuracao (1-3),
        state_registration and service_code; they are the company
        owner's alone, and anyone else gets an APIError 403.

        Only what is given is sent; a call with nothing changes nothing.
        Returns every readiness() field plus `address` and
        `fiscal_fields` as stored. An OAuth credential needs
        company:write.
        """
        payload: dict[str, Any] = {}
        if address is not None:
            fields = _group("address", address, ADDRESS_FIELDS)
            code = fields.get("municipality_code")
            if code is not None and not re.fullmatch(r"[0-9]{7}", code):
                raise ValueError("municipality_code must be the 7-digit IBGE code")
            if "zip_code" in fields:
                digits = re.sub(r"[\s.-]", "", fields["zip_code"])
                if not re.fullmatch(r"[0-9]{8}", digits):
                    raise ValueError("zip_code must be the 8-digit CEP")
                fields["zip_code"] = digits
            if fields:
                payload["address"] = fields
        if fiscal_fields is not None:
            fields = _group("fiscal_fields", fiscal_fields, FISCAL_FIELDS)
            for key, allowed in _ENUMS.items():
                if key in fields and fields[key] not in allowed:
                    raise ValueError(f"{key} must be one of {', '.join(allowed)}")
            if fields:
                payload["fiscal_fields"] = fields

        return cast(
            dict,
            self._request("PATCH", "/company", json=payload, company=company),
        )


def _group(
    name: str, given: Mapping[str, str | None], allowed: tuple[str, ...]
) -> dict[str, str]:
    """`given` without its None values, refusing a key the API refuses."""
    unknown = sorted(set(given) - set(allowed))
    if unknown:
        raise ValueError(
            f"unknown {name} fields: {', '.join(unknown)}. "
            f"Known: {', '.join(allowed)}"
        )
    return {key: value for key, value in given.items() if value is not None}
