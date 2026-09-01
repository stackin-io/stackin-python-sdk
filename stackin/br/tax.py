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


class Icms60(BaseModel):
    """ICMS already charged by an earlier substitution."""

    model_config = _CONFIG

    orig: str
    cst: str = Field(default="60", alias="CST")
    v_bc_st_ret: str | None = Field(default=None, alias="vBCSTRet")
    p_st: str | None = Field(default=None, alias="pST")
    v_icms_substituto: str | None = Field(
        default=None, alias="vICMSSubstituto"
    )
    v_icms_st_ret: str | None = Field(default=None, alias="vICMSSTRet")
    v_bc_fcp_st_ret: str | None = Field(default=None, alias="vBCFCPSTRet")
    p_fcp_st_ret: str | None = Field(default=None, alias="pFCPSTRet")
    v_fcp_st_ret: str | None = Field(default=None, alias="vFCPSTRet")
    p_red_bc_efet: str | None = Field(default=None, alias="pRedBCEfet")
    v_bc_efet: str | None = Field(default=None, alias="vBCEfet")
    p_icms_efet: str | None = Field(default=None, alias="pICMSEfet")
    v_icms_efet: str | None = Field(default=None, alias="vICMSEfet")


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


class IcmsSn900(BaseModel):
    """Simples Nacional ICMS, other cases (used with interstate partilha)."""

    model_config = _CONFIG

    orig: str | None = None
    csosn: str = Field(default="900", alias="CSOSN")
    mod_bc: str | None = Field(default=None, alias="modBC")
    v_bc: str | None = Field(default=None, alias="vBC")
    p_icms: str | None = Field(default=None, alias="pICMS")
    v_icms: str | None = Field(default=None, alias="vICMS")


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


class IpiTrib(BaseModel):
    """IPI taxed by rate."""

    model_config = _CONFIG

    cst: Literal["00", "49", "50", "99"] = Field(alias="CST")
    v_bc: str | None = Field(default=None, alias="vBC")
    p_ipi: str | None = Field(default=None, alias="pIPI")
    q_unid: str | None = Field(default=None, alias="qUnid")
    v_unid: str | None = Field(default=None, alias="vUnid")
    v_ipi: str = Field(alias="vIPI")


class IpiNt(BaseModel):
    """IPI not taxed."""

    model_config = _CONFIG

    cst: str = Field(alias="CST")


IpiVariant = IpiTrib | IpiNt | dict[str, Any]
_IPI_TAGS = {IpiTrib: "IPITrib", IpiNt: "IPINT"}


class Ipi(BaseModel):
    """This item's IPI."""

    model_config = _CONFIG

    c_enq: str = Field(alias="cEnq")
    trib: IpiVariant

    def to_dict(self) -> dict:
        """Returns the IPI group as a plain dict."""
        data = {"cEnq": self.c_enq}
        data.update(_wrap(self.trib, _IPI_TAGS))
        return data


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


class PisOutr(BaseModel):
    """PIS taxed some other way."""

    model_config = _CONFIG

    cst: str = Field(alias="CST")
    v_bc: str | None = Field(default=None, alias="vBC")
    p_pis: str | None = Field(default=None, alias="pPIS")
    v_pis: str = Field(alias="vPIS")


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


class CofinsOutr(BaseModel):
    """COFINS taxed some other way."""

    model_config = _CONFIG

    cst: str = Field(alias="CST")
    v_bc: str | None = Field(default=None, alias="vBC")
    p_cofins: str | None = Field(default=None, alias="pCOFINS")
    v_cofins: str = Field(alias="vCOFINS")


IcmsGroup = (
    Icms00 | Icms40 | Icms60 | IcmsSn101 | IcmsSn102 | IcmsSn900 | dict[str, Any]
)
PisGroup = PisAliq | PisNt | PisOutr | dict[str, Any]
CofinsGroup = CofinsAliq | CofinsNt | CofinsOutr | dict[str, Any]

_ICMS_TAGS = {
    Icms00: "ICMS00",
    Icms40: "ICMS40",
    Icms60: "ICMS60",
    IcmsSn101: "ICMSSN101",
    IcmsSn102: "ICMSSN102",
    IcmsSn900: "ICMSSN900",
}
_PIS_TAGS = {PisAliq: "PISAliq", PisNt: "PISNT", PisOutr: "PISOutr"}
_COFINS_TAGS = {
    CofinsAliq: "COFINSAliq",
    CofinsNt: "COFINSNT",
    CofinsOutr: "COFINSOutr",
}


class Tax(BaseModel):
    """This item's taxes, already computed by the caller."""

    model_config = _CONFIG

    v_tot_trib: str | None = Field(default=None, alias="vTotTrib")
    icms: IcmsGroup | None = None
    icms_uf_dest: IcmsUfDest | None = None
    ipi: Ipi | dict[str, Any] | None = None
    pis: PisGroup | None = None
    cofins: CofinsGroup | None = None

    def to_dict(self) -> dict:
        """Returns the taxes as a plain dict."""
        data: dict[str, Any] = {}
        if self.v_tot_trib is not None:
            data["vTotTrib"] = self.v_tot_trib
        if self.icms is not None:
            data["ICMS"] = _wrap(self.icms, _ICMS_TAGS)
        if self.icms_uf_dest is not None:
            data["ICMSUFDest"] = self.icms_uf_dest.model_dump(
                by_alias=True, exclude_none=True
            )
        if self.ipi is not None:
            data["IPI"] = (
                self.ipi.to_dict() if isinstance(self.ipi, Ipi) else self.ipi
            )
        if self.pis is not None:
            data["PIS"] = _wrap(self.pis, _PIS_TAGS)
        if self.cofins is not None:
            data["COFINS"] = _wrap(self.cofins, _COFINS_TAGS)
        return data


def _wrap(group: BaseModel | dict, tags: dict[type, str]) -> dict:
    """Nests a tax group under its variant name."""
    if isinstance(group, dict):
        return group
    return {
        tags[type(group)]: group.model_dump(by_alias=True, exclude_none=True)
    }
