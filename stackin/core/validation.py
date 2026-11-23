"""The answer of a dry run: `Invoice.validate`."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Finding(BaseModel):
    """One rule the document broke, or one warning about it.

    `field` is the request path to fix (None when no single field is at
    fault), `sefaz_rejection` the cStat the authority would have answered
    and `fix_url` where the company fixes it. A warning carries only
    `code` and `message`.
    """

    model_config = ConfigDict(extra="ignore")

    code: str
    message: str
    field: str | None = None
    sefaz_rejection: str | None = None
    expected: Any = None
    received: Any = None
    fix_url: str | None = None


class ValidationResult(BaseModel):
    """Whether the document would go through, and why not.

    Nothing was transmitted, numbered or charged. `valid` is False when
    `errors` is not empty; `warnings` are listed either way.
    """

    model_config = ConfigDict(extra="ignore")

    valid: bool
    errors: list[Finding] = Field(default_factory=list)
    warnings: list[Finding] = Field(default_factory=list)
