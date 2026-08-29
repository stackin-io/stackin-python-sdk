"""Product module — Brazil-specific, see `invoice.core.br`."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PresumedCredit(BaseModel):
    """`det/prod/gCred` — presumed ICMS credit / state tax benefit
    applied to this item, up to 4 per item."""

    code: str
    percentage: float
    amount: float


class Product(BaseModel):
    """
    One line item — pass a list of these as `issue()`'s `items`; one
    entry even for a single product/service. NFe emits one `det` per
    item; NFSe (a single service) only uses the first.

    `ncm`/`cfop`/... are Brazilian tax classification codes (Receita
    Federal's NCM table, SINIEF's CFOP table) with no equivalent in
    NFSE or in any other country's fiscal documents — don't reuse
    this class outside a Brazil/NFE context.

    `issue()` requires `ncm` and `cfop` when `document_type` is NFE.

    Covers the full `det/prod` XSD group: commonly-used fields are
    typed below; the vertical-specific groups that only apply to a
    handful of business types (import/export declarations, vehicles,
    medicine, weapons, fuel, batch/lot tracking) go in `extra_groups`
    — a passthrough dict keyed by their exact XSD tag name (`DI`,
    `detExport`, `rastro`, `veicProd`, `med`, `arma`, `comb`). None of
    this is validated by the SDK — invoice-api and the authorizer's
    own schema/business rules are the real check.

    Args:
        description (str): Service/product description.
        amount (float): Item's amount.
        ncm (str | None): NCM code (8 digits, or "00" for services/
            non-goods).
        cfop (str | None): CFOP code for this operation.
        unit (str): Commercial unit. Default "UN".
        quantity (float): Commercial quantity. Default 1 (the unit
            price is then just `amount`).
        barcode (str | None): cEAN/cEANTrib — real GTIN/barcode,
            overrides the "SEM GTIN" default.
        cest (str | None): CEST — required only for ICMS-ST items.
        nve_codes (list[str] | None): NVE — customs valuation/
            statistical nomenclature codes, up to 8.
        ind_escala (str | None): indEscala — "S"/"N", relevant-scale
            manufacturing indicator.
        manufacturer_cnpj (str | None): CNPJFab — required when
            ind_escala="N".
        tax_benefit_code (str | None): cBenef.
        presumed_credits (list[PresumedCredit] | None): gCred, up to 4.
        ex_tipi (str | None): EXTIPI.
        freight (float | None): vFrete for this item.
        insurance (float | None): vSeg for this item.
        discount (float | None): vDesc for this item.
        other_expenses (float | None): vOutro for this item.
        used_movable_asset (bool): indBemMovelUsado.
        purchase_order (str | None): xPed.
        purchase_order_item (str | None): nItemPed.
        import_content_control_number (str | None): nFCI — Ficha de
            Conteúdo de Importação.
        recopi_number (str | None): nRECOPI — paper subject to
            RECOPI control.
        extra_groups (dict[str, Any] | None): Passthrough for
            det/prod's vertical-specific groups (DI, detExport,
            rastro, veicProd, med, arma, comb), keyed by their exact
            XSD tag name.
        tax (dict[str, Any] | None): Passthrough for det/imposto.
    """

    description: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    ncm: str | None = Field(default=None)
    cfop: str | None = Field(default=None)
    unit: str = Field(default="UN")
    quantity: float = Field(default=1.0, gt=0)
    barcode: str | None = Field(default=None)
    cest: str | None = Field(default=None)
    nve_codes: list[str] | None = Field(default=None)
    ind_escala: str | None = Field(default=None)
    manufacturer_cnpj: str | None = Field(default=None)
    tax_benefit_code: str | None = Field(default=None)
    presumed_credits: list[PresumedCredit] | None = Field(default=None)
    ex_tipi: str | None = Field(default=None)
    freight: float | None = Field(default=None)
    insurance: float | None = Field(default=None)
    discount: float | None = Field(default=None)
    other_expenses: float | None = Field(default=None)
    used_movable_asset: bool = Field(default=False)
    purchase_order: str | None = Field(default=None)
    purchase_order_item: str | None = Field(default=None)
    import_content_control_number: str | None = Field(default=None)
    recopi_number: str | None = Field(default=None)
    extra_groups: dict[str, Any] | None = Field(default=None)
    tax: dict[str, Any] | None = Field(default=None)

    def to_dict(self) -> dict:
        """Return the item as a plain dict, ready for the request
        body — `description`/`amount` at the top, everything else
        nested under `product` (invoice-api's `IssueRequest` shape).
        Fields left unset are omitted, not sent as null."""
        data = self.model_dump(exclude_none=True, exclude={"description", "amount"})
        return {"description": self.description, "amount": self.amount, "product": data}
