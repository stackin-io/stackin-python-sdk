"""Types module."""

from __future__ import annotations

from enum import Enum


class DocumentType(str, Enum):
    """Fiscal document type to issue/consult/cancel."""

    NFE = "nfe"
    NFSE = "nfse"
