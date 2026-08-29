"""Types module."""

from __future__ import annotations

from enum import Enum


class DocumentType(str, Enum):
    """The kind of fiscal document to issue, consult, or cancel."""

    NFE = "nfe"
    NFSE = "nfse"
