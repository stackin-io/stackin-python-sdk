"""The IBS/CBS simulation of `POST /ibs-cbs/calculate`.

Requests refuse unknown fields, as the API does. Responses ignore the
ones the API adds later, so an older SDK keeps reading a newer API.
Amounts and rates arrive as decimal strings and stay strings.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class IbsCbsRates(BaseModel):
    """Rates for every item of a simulation, in percent."""

    model_config = ConfigDict(extra="forbid")

    rate_state: float | None = Field(default=None, ge=0, le=100, description="pIBSUF.")
    rate_city: float | None = Field(default=None, ge=0, le=100, description="pIBSMun.")
    rate_federal: float | None = Field(default=None, ge=0, le=100, description="pCBS.")


class IbsCbsCalculationItem(IbsCbsRates):
    """One item to simulate. Its own rates win over the request's."""

    cst: str = Field(pattern=r"^\d{3}$", description="CST of IBS/CBS.")
    classification: str = Field(pattern=r"^\d{6}$", description="cClassTrib.")
    amount: float | None = Field(
        default=None, gt=0, description="The item amount; the base without `base`."
    )
    base: float | None = Field(default=None, gt=0, description="vBC.")
    reduction_ibs: float | None = Field(
        default=None, ge=0, le=100, description="pRedAliq of the IBS."
    )
    reduction_cbs: float | None = Field(
        default=None, ge=0, le=100, description="pRedAliq of the CBS."
    )

    @model_validator(mode="after")
    def _needs_a_base(self) -> IbsCbsCalculationItem:
        if self.amount is None and self.base is None:
            raise ValueError("send amount or base")
        return self


class IbsCbsIndicators(BaseModel):
    """The CST's ind_gIBSCBS, ind_gRed and ind_gDif."""

    model_config = ConfigDict(extra="ignore")

    group: int | None = None
    reduction: int | None = None
    deferral: int | None = None


class IbsCbsAppliedRates(BaseModel):
    """pIBSUF, pIBSMun and pCBS as applied, in percent."""

    model_config = ConfigDict(extra="ignore")

    rate_state: str
    rate_city: str
    rate_federal: str


class IbsCbsAmounts(BaseModel):
    """The amounts of one item, or of the whole simulation."""

    model_config = ConfigDict(extra="ignore")

    base: str
    ibs_state: str
    ibs_city: str
    ibs: str
    cbs: str
    deferred_ibs_state: str
    deferred_ibs_city: str
    deferred_cbs: str


class IbsCbsCalculatedItem(BaseModel):
    """What the NF-e IBSCBS group of one item would carry."""

    model_config = ConfigDict(extra="ignore")

    cst: str
    classification: str
    indicators: IbsCbsIndicators
    has_group: bool
    rates: IbsCbsAppliedRates | None = None
    rates_source: Literal["caller", "official_2026"] | None = None
    reduction_ibs: str | None = None
    reduction_cbs: str | None = None
    effective_rates: IbsCbsAppliedRates | None = None
    deferral: str | None = None
    amounts: IbsCbsAmounts


class IbsCbsCalculation(BaseModel):
    """A simulation: not a fiscal document, nothing issued or stored."""

    model_config = ConfigDict(extra="ignore")

    simulated: bool = True
    notice: str
    document_type: str
    operation_date: date
    items: list[IbsCbsCalculatedItem]
    total: IbsCbsAmounts
