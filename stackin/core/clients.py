"""The company's saved clients: the recipients it issues to again.

Company data, like everything on Invoice, so every method takes
`company` for one call over the client's own. The rules on a client's
fields are the issuance's own (a CPF/CNPJ that checks out, a buyer
abroad identified by foreign_id) and they are the API's: a refusal
comes back as an APIError 422, not as a guess made here.
"""

from __future__ import annotations

from typing import Any, Final, cast

from stackin.core.address import Address
from stackin.core.client import _Client
from stackin.core.reference import _segment


class _Unset:
    """Marks an update() field the caller did not pass."""

    def __repr__(self) -> str:
        return "UNSET"


_UNSET: Final = _Unset()


def _address_dict(address: Address | dict | None) -> dict | None:
    if address is None or isinstance(address, dict):
        return address
    return address.to_dict()


class Clients(_Client):
    """Client for the company's client registry, `/clients`."""

    def list(
        self,
        *,
        search: str | None = None,
        source: str | None = None,
        is_active: bool | None = None,
        limit: int | None = None,
        offset: int | None = None,
        sort_by: str | None = None,
        order_by: str | None = None,
        company: str | None = None,
    ) -> dict:
        """A page of the company's clients, by name unless sort_by says
        otherwise.

        `search` matches part of the name, the tax id (masked or not) or
        the foreign_id. `source` is manual, issued or issuance. The API
        lists active clients when `is_active` is left out; False lists
        the deactivated ones. `sort_by` takes name, last_used_at,
        created_at or uses_count.
        """
        params: dict[str, Any] = {}
        if search:
            params["search"] = search
        if source is not None:
            params["source"] = source
        if is_active is not None:
            params["is_active"] = "true" if is_active else "false"
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if sort_by is not None:
            params["sort_by"] = sort_by
        if order_by is not None:
            params["order_by"] = order_by

        return cast(
            dict,
            self._request("GET", "/clients", params=params, company=company),
        )

    def get(self, client_id: str, *, company: str | None = None) -> dict:
        """One client, deactivated or not. Another company's is a 404."""
        return cast(
            dict,
            self._request("GET", f"/clients/{_segment(client_id)}", company=company),
        )

    def create(
        self,
        *,
        name: str,
        tax_id: str | None = None,
        foreign_id: str | None = None,
        state_registration: str | None = None,
        municipal_registration: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        address: Address | dict | None = None,
        notes: str | None = None,
        company: str | None = None,
    ) -> dict:
        """Saves a client by hand.

        A tax_id or foreign_id the company already holds raises
        ClientAlreadyExistsError, whose `client_id` names that client.
        Each field left as None is left out of the body.
        """
        fields = {
            "name": name,
            "tax_id": tax_id,
            "foreign_id": foreign_id,
            "state_registration": state_registration,
            "municipal_registration": municipal_registration,
            "email": email,
            "phone": phone,
            "address": _address_dict(address),
            "notes": notes,
        }
        payload = {key: value for key, value in fields.items() if value is not None}

        return cast(
            dict,
            self._request("POST", "/clients", json=payload, company=company),
        )

    def update(
        self,
        client_id: str,
        *,
        name: str | _Unset = _UNSET,
        tax_id: str | None | _Unset = _UNSET,
        foreign_id: str | None | _Unset = _UNSET,
        state_registration: str | None | _Unset = _UNSET,
        municipal_registration: str | None | _Unset = _UNSET,
        email: str | None | _Unset = _UNSET,
        phone: str | None | _Unset = _UNSET,
        address: Address | dict | None | _Unset = _UNSET,
        notes: str | None | _Unset = _UNSET,
        is_active: bool | _Unset = _UNSET,
        company: str | None = None,
    ) -> dict:
        """Changes only the fields passed; None clears one.

        `address` replaces the whole address. The API checks the result
        as a whole, so clearing the tax_id of a Brazilian client is
        refused like a create without one. Taking another client's
        tax_id raises ClientAlreadyExistsError.
        """
        fields: dict[str, Any] = {
            "name": name,
            "tax_id": tax_id,
            "foreign_id": foreign_id,
            "state_registration": state_registration,
            "municipal_registration": municipal_registration,
            "email": email,
            "phone": phone,
            "address": address,
            "notes": notes,
            "is_active": is_active,
        }
        payload = {key: value for key, value in fields.items() if value is not _UNSET}
        if "address" in payload:
            payload["address"] = _address_dict(payload["address"])

        return cast(
            dict,
            self._request(
                "PATCH",
                f"/clients/{_segment(client_id)}",
                json=payload,
                company=company,
            ),
        )

    def deactivate(self, client_id: str, *, company: str | None = None) -> None:
        """Deactivates a client. It is kept, and reactivate() brings it back.

        A deactivated client is left out of list() by default, and
        issuing with its client_id is refused until it is reactivated.
        """
        self._send("DELETE", f"/clients/{_segment(client_id)}", company=company)

    def reactivate(self, client_id: str, *, company: str | None = None) -> dict:
        """Brings a deactivated client back; returns it."""
        return self.update(client_id, is_active=True, company=company)
