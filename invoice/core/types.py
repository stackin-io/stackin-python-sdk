"""Types module."""

from __future__ import annotations

from enum import Enum


class DocumentType(str, Enum):
    """Fiscal document type to issue/consult/cancel. Doubles as the
    jurisdiction selector: NFE/NFSE are Brazilian (SEFAZ/UF, national
    ADN); FACTURA is Argentina's WSFEv1 — wired end to end but always
    fails today (no confirmed WSAA/WSFEv1 host, see
    invoice-api/plan/ARGENTINA.md)."""

    NFE = "nfe"
    NFSE = "nfse"
    FACTURA = "factura"
