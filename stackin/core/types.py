"""Types module."""

from __future__ import annotations

from enum import Enum


class DocumentType(str, Enum):
    """The kind of fiscal document to issue, consult, or cancel."""

    NFE = "nfe"
    NFSE = "nfse"


class Environment(str, Enum):
    """Which host to talk to — pass to `Invoice(environment=...)` instead of a raw `base_url`."""

    LOCAL = "local"
    TEST = "test"
    PRODUCTION = "production"
