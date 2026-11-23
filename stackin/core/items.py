"""The company's catalog of products and services, reused when issuing.

Company data, like everything on Invoice, so every method takes
`company` for one call over the client's own. The rules on an item's
fields (the NCM, the CFOP, a GTIN that checks out, an LC 116 service
code) are the API's: a refusal comes back as an APIError 422, not as a
guess made here.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from decimal import Decimal
from typing import Any, TypedDict, cast

from stackin.core.client import _Client
from stackin.core.clients import _UNSET, _Unset
from stackin.core.reference import _segment

_UPSERT_FIELDS = (
    "kind",
    "description",
    "code",
    "unit_price",
    "unit",
    "external_reference",
    "notes",
    "ncm",
    "cfop",
    "tax_situation",
    "origin",
    "cest",
    "gtin",
    "service_code",
    "iss_retained",
    "net_weight",
    "gross_weight",
    "ibs_cbs_cst",
    "ibs_cbs_class",
)


class CatalogItem(TypedDict):
    """An item as the API returns it, on every read and write."""

    id: str
    company_id: str
    kind: str
    description: str
    code: str | None
    unit_price: float
    unit: str | None
    source: str
    external_reference: str | None
    notes: str | None
    ncm: str | None
    cfop: str | None
    tax_situation: str | None
    origin: str | None
    cest: str | None
    gtin: str | None
    service_code: str | None
    iss_retained: bool | None
    net_weight: float | None
    gross_weight: float | None
    ibs_cbs_cst: str | None
    ibs_cbs_class: str | None
    is_active: bool
    uses_count: int
    last_used_at: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class ItemSaved:
    """What `Items.upsert()` answers: the item, and whether it is new.

    `created` is True for the API's 201 and False for its 200, an
    existing item that the call updated.
    """

    item: CatalogItem
    created: bool


def _price(value: Decimal | float | int | str | None) -> Any:
    """A Decimal as a string: JSON has no decimal, a float would round."""
    return format(value, "f") if isinstance(value, Decimal) else value


def _check_weight(name: str, value: Decimal | float | int | str | None) -> None:
    if value is None:
        return
    try:
        weight = Decimal(str(value))
    except ArithmeticError:
        raise ValueError(f"{name} must be a number") from None
    if not weight.is_finite() or weight < 0:
        raise ValueError(f"{name} must be 0 or more")


def _check_ibs_cbs(cst: str | None, classification: str | None) -> None:
    if cst is not None and not re.fullmatch(r"\d{3}", cst):
        raise ValueError("ibs_cbs_cst must be 3 digits")
    if classification is not None and not re.fullmatch(r"\d{6}", classification):
        raise ValueError("ibs_cbs_class must be 6 digits")


class Items(_Client):
    """Client for the company's catalog, `/items`."""

    def list(
        self,
        *,
        kind: str | None = None,
        search: str | None = None,
        source: str | None = None,
        is_active: bool | None = None,
        limit: int | None = None,
        offset: int | None = None,
        sort_by: str | None = None,
        order_by: str | None = None,
        company: str | None = None,
    ) -> dict:
        """A page of the company's items, by description unless sort_by
        says otherwise.

        `kind` is product or service. `search` matches part of the
        description, code or external_reference; digits also match the
        ncm and gtin. `source` is manual, import, nuvemshop or invoice.
        The API lists active items when `is_active` is left out; False
        lists the deactivated ones. `sort_by` takes description, code,
        unit_price, last_used_at, created_at or uses_count.
        """
        params: dict[str, Any] = {}
        if kind is not None:
            params["kind"] = kind
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
            self._request("GET", "/items", params=params, company=company),
        )

    def get(self, item_id: str, *, company: str | None = None) -> CatalogItem:
        """One item, deactivated or not. Another company's is a 404."""
        return cast(
            CatalogItem,
            self._request("GET", f"/items/{_segment(item_id)}", company=company),
        )

    def create(
        self,
        *,
        kind: str,
        description: str,
        code: str | None = None,
        unit_price: Decimal | float | int | str | None = None,
        unit: str | None = None,
        external_reference: str | None = None,
        notes: str | None = None,
        ncm: str | None = None,
        cfop: str | None = None,
        tax_situation: str | None = None,
        origin: str | None = None,
        cest: str | None = None,
        gtin: str | None = None,
        service_code: str | None = None,
        iss_retained: bool | None = None,
        net_weight: Decimal | float | int | str | None = None,
        gross_weight: Decimal | float | int | str | None = None,
        ibs_cbs_cst: str | None = None,
        ibs_cbs_class: str | None = None,
        source: str | None = None,
        company: str | None = None,
    ) -> CatalogItem:
        """Saves an item; returns it.

        This is the API's upsert (POST /items): an item the company
        already has with the same `external_reference`, or the same
        `code` when none is sent, is updated with the fields passed
        instead of duplicated, so sending the same call twice never makes
        two items. Use upsert() to learn which of the two happened.
        A `code` or `external_reference` that belongs to a different item
        raises ItemAlreadyExistsError, whose `item_id` names it.

        `kind` is product (NF-e) or service (NFS-e) and decides which
        fiscal fields apply: ncm, cfop, tax_situation, origin, cest and
        gtin for a product, service_code and iss_retained for a service.
        `net_weight` and `gross_weight` (kg per unit) are product-only and fill the issuance line's weights;
        `ibs_cbs_cst` and `ibs_cbs_class` fill its IBS/CBS
        group. `source` (manual by default) is kept only when the item is
        new. Each field left as None is left out of the body.
        """
        return self.upsert(
            kind=kind,
            description=description,
            code=code,
            unit_price=unit_price,
            unit=unit,
            external_reference=external_reference,
            notes=notes,
            ncm=ncm,
            cfop=cfop,
            tax_situation=tax_situation,
            origin=origin,
            cest=cest,
            gtin=gtin,
            service_code=service_code,
            iss_retained=iss_retained,
            net_weight=net_weight,
            gross_weight=gross_weight,
            ibs_cbs_cst=ibs_cbs_cst,
            ibs_cbs_class=ibs_cbs_class,
            source=source,
            company=company,
        ).item

    def upsert(
        self,
        *,
        kind: str,
        description: str,
        code: str | None = None,
        unit_price: Decimal | float | int | str | None = None,
        unit: str | None = None,
        external_reference: str | None = None,
        notes: str | None = None,
        ncm: str | None = None,
        cfop: str | None = None,
        tax_situation: str | None = None,
        origin: str | None = None,
        cest: str | None = None,
        gtin: str | None = None,
        service_code: str | None = None,
        iss_retained: bool | None = None,
        net_weight: Decimal | float | int | str | None = None,
        gross_weight: Decimal | float | int | str | None = None,
        ibs_cbs_cst: str | None = None,
        ibs_cbs_class: str | None = None,
        source: str | None = None,
        company: str | None = None,
    ) -> ItemSaved:
        """Like create(), but says whether the item was created.

        `ItemSaved.created` is True when the API answered 201 (a new
        item) and False when it answered 200 (an existing one, updated).
        """
        values: dict[str, Any] = {
            "kind": kind,
            "description": description,
            "code": code,
            "unit_price": _price(unit_price),
            "unit": unit,
            "external_reference": external_reference,
            "notes": notes,
            "ncm": ncm,
            "cfop": cfop,
            "tax_situation": tax_situation,
            "origin": origin,
            "cest": cest,
            "gtin": gtin,
            "service_code": service_code,
            "iss_retained": iss_retained,
            "net_weight": _price(net_weight),
            "gross_weight": _price(gross_weight),
            "ibs_cbs_cst": ibs_cbs_cst,
            "ibs_cbs_class": ibs_cbs_class,
        }
        _check_weight("net_weight", net_weight)
        _check_weight("gross_weight", gross_weight)
        _check_ibs_cbs(ibs_cbs_cst, ibs_cbs_class)
        payload = {
            key: values[key] for key in _UPSERT_FIELDS if values[key] is not None
        }
        if source is not None:
            payload["source"] = source

        response = self._send("POST", "/items", json=payload, company=company)
        body = response.json() if response.content else {}
        if isinstance(body, dict):
            body = body.get("result", body)
        return ItemSaved(
            item=cast(CatalogItem, body), created=response.status_code == 201
        )

    def update(
        self,
        item_id: str,
        *,
        kind: str | _Unset = _UNSET,
        description: str | _Unset = _UNSET,
        code: str | None | _Unset = _UNSET,
        unit_price: Decimal | float | int | str | _Unset = _UNSET,
        unit: str | None | _Unset = _UNSET,
        external_reference: str | None | _Unset = _UNSET,
        notes: str | None | _Unset = _UNSET,
        ncm: str | None | _Unset = _UNSET,
        cfop: str | None | _Unset = _UNSET,
        tax_situation: str | None | _Unset = _UNSET,
        origin: str | None | _Unset = _UNSET,
        cest: str | None | _Unset = _UNSET,
        gtin: str | None | _Unset = _UNSET,
        service_code: str | None | _Unset = _UNSET,
        iss_retained: bool | None | _Unset = _UNSET,
        net_weight: Decimal | float | int | str | None | _Unset = _UNSET,
        gross_weight: Decimal | float | int | str | None | _Unset = _UNSET,
        ibs_cbs_cst: str | None | _Unset = _UNSET,
        ibs_cbs_class: str | None | _Unset = _UNSET,
        is_active: bool | _Unset = _UNSET,
        company: str | None = None,
    ) -> CatalogItem:
        """Changes only the fields passed; None clears one.

        `source` is set on creation and never changes. The API checks the
        result as a whole, so turning a product into a service while it
        still has an ncm is refused (422). Taking the code or
        external_reference of another item raises ItemAlreadyExistsError.
        """
        fields: dict[str, Any] = {
            "kind": kind,
            "description": description,
            "code": code,
            "unit_price": unit_price,
            "unit": unit,
            "external_reference": external_reference,
            "notes": notes,
            "ncm": ncm,
            "cfop": cfop,
            "tax_situation": tax_situation,
            "origin": origin,
            "cest": cest,
            "gtin": gtin,
            "service_code": service_code,
            "iss_retained": iss_retained,
            "net_weight": net_weight,
            "gross_weight": gross_weight,
            "ibs_cbs_cst": ibs_cbs_cst,
            "ibs_cbs_class": ibs_cbs_class,
            "is_active": is_active,
        }
        payload = {key: value for key, value in fields.items() if value is not _UNSET}
        for key in ("unit_price", "net_weight", "gross_weight"):
            if key in payload:
                payload[key] = _price(payload[key])
        for key in ("net_weight", "gross_weight"):
            if isinstance(fields[key], _Unset):
                continue
            _check_weight(key, fields[key])
        if not isinstance(ibs_cbs_cst, _Unset) or not isinstance(ibs_cbs_class, _Unset):
            _check_ibs_cbs(
                None if isinstance(ibs_cbs_cst, _Unset) else ibs_cbs_cst,
                None if isinstance(ibs_cbs_class, _Unset) else ibs_cbs_class,
            )

        return cast(
            CatalogItem,
            self._request(
                "PATCH",
                f"/items/{_segment(item_id)}",
                json=payload,
                company=company,
            ),
        )

    def deactivate(self, item_id: str, *, company: str | None = None) -> None:
        """Deactivates an item. It is kept, and reactivate() brings it back.

        A deactivated item is left out of list() by default, still holds
        its code, and issuing with its item_id is refused until it is
        reactivated.
        """
        self._send("DELETE", f"/items/{_segment(item_id)}", company=company)

    def reactivate(self, item_id: str, *, company: str | None = None) -> CatalogItem:
        """Brings a deactivated item back; returns it."""
        return self.update(item_id, is_active=True, company=company)
