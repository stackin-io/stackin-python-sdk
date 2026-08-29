"""Tax module."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

_CONFIG = ConfigDict(populate_by_name=True)


class Icms00(BaseModel):
    """ICMS fully taxed."""

    model_config = _CONFIG

    orig: str
    cst: str = Field(default="00", alias="CST")
    mod_bc: str = Field(alias="modBC")
    v_bc: str = Field(alias="vBC")
    p_icms: str = Field(alias="pICMS")
    v_icms: str = Field(alias="vICMS")
    p_fcp: str | None = Field(default=None, alias="pFCP")
    v_fcp: str | None = Field(default=None, alias="vFCP")


class Icms40(BaseModel):
    """ICMS exempt or not taxed."""

    model_config = _CONFIG

    orig: str
    cst: str = Field(alias="CST")
    v_icms_deson: str | None = Field(default=None, alias="vICMSDeson")
    mot_des_icms: str | None = Field(default=None, alias="motDesICMS")


class IcmsSn101(BaseModel):
    """Simples Nacional ICMS with a credit."""

    model_config = _CONFIG

    orig: str
    csosn: str = Field(default="101", alias="CSOSN")
    p_cred_sn: str = Field(alias="pCredSN")
    v_cred_icms_sn: str = Field(alias="vCredICMSSN")


class IcmsSn102(BaseModel):
    """Simples Nacional ICMS without a credit."""

    model_config = _CONFIG

    orig: str | None = None
    csosn: str = Field(alias="CSOSN")


class IcmsUfDest(BaseModel):
    """Interstate ICMS share owed to the destination state."""

    model_config = _CONFIG

    v_bc_uf_dest: str = Field(alias="vBCUFDest")
    v_bc_fcp_uf_dest: str | None = Field(default=None, alias="vBCFCPUFDest")
    p_fcp_uf_dest: str | None = Field(default=None, alias="pFCPUFDest")
    p_icms_uf_dest: str = Field(alias="pICMSUFDest")
    p_icms_inter: Literal["4.00", "7.00", "12.00"] = Field(alias="pICMSInter")
    p_icms_inter_part: str = Field(alias="pICMSInterPart")
    v_fcp_uf_dest: str | None = Field(default=None, alias="vFCPUFDest")
    v_icms_uf_dest: str = Field(alias="vICMSUFDest")
    v_icms_uf_remet: str = Field(alias="vICMSUFRemet")


class PisAliq(BaseModel):
    """PIS taxed by rate."""

    model_config = _CONFIG

    cst: str = Field(alias="CST")
    v_bc: str = Field(alias="vBC")
    p_pis: str = Field(alias="pPIS")
    v_pis: str = Field(alias="vPIS")


class PisNt(BaseModel):
    """PIS not taxed."""

    model_config = _CONFIG

    cst: str = Field(alias="CST")


class CofinsAliq(BaseModel):
    """COFINS taxed by rate."""

    model_config = _CONFIG

    cst: str = Field(alias="CST")
    v_bc: str = Field(alias="vBC")
    p_cofins: str = Field(alias="pCOFINS")
    v_cofins: str = Field(alias="vCOFINS")


class CofinsNt(BaseModel):
    """COFINS not taxed."""

    model_config = _CONFIG

    cst: str = Field(alias="CST")


IcmsGroup = Icms00 | Icms40 | IcmsSn101 | IcmsSn102 | dict[str, Any]
PisGroup = PisAliq | PisNt | dict[str, Any]
CofinsGroup = CofinsAliq | CofinsNt | dict[str, Any]

_ICMS_TAGS = {
    Icms00: "ICMS00",
    Icms40: "ICMS40",
    IcmsSn101: "ICMSSN101",
    IcmsSn102: "ICMSSN102",
}
_PIS_TAGS = {PisAliq: "PISAliq", PisNt: "PISNT"}
_COFINS_TAGS = {CofinsAliq: "COFINSAliq", CofinsNt: "COFINSNT"}


class Tax(BaseModel):
    """This item's taxes, already computed by the caller."""

    icms: IcmsGroup | None = None
    icms_uf_dest: IcmsUfDest | None = None
    pis: PisGroup | None = None
    cofins: CofinsGroup | None = None
    ipi: dict[str, Any] | None = None

    def to_dict(self) -> dict:
        """Returns the taxes as a plain dict."""
        data: dict[str, Any] = {}
        if self.icms is not None:
            data["ICMS"] = _wrap(self.icms, _ICMS_TAGS)
        if self.icms_uf_dest is not None:
            data["ICMSUFDest"] = self.icms_uf_dest.model_dump(
                by_alias=True, exclude_none=True
            )
        if self.pis is not None:
            data["PIS"] = _wrap(self.pis, _PIS_TAGS)
        if self.cofins is not None:
            data["COFINS"] = _wrap(self.cofins, _COFINS_TAGS)
        if self.ipi is not None:
            data["IPI"] = self.ipi
        return data


def _wrap(group: BaseModel | dict, tags: dict[type, str]) -> dict:
    """Nests a tax group under its variant name."""
    if isinstance(group, dict):
        return group
    return {tags[type(group)]: group.model_dump(by_alias=True, exclude_none=True)}
