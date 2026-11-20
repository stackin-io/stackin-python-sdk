"""Where the company's events are delivered: `/webhooks`.

Company data, so every method takes `company` for one call over the
client's own. An endpoint receives the events of the credential's own
environment only. Every call needs the `webhook:manage` permission on an
OAuth credential; an API key has it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, cast

from stackin.core.client import _Client, _page_params
from stackin.core.reference import _segment

EVENTS = (
    "invoice.authorized",
    "invoice.rejected",
    "invoice.cancelled",
    "invoice.corrected",
)

_SECRET_MIN = 16
_SECRET_MAX = 255
_URL_MAX = 500


class Webhooks(_Client):
    """Client for the company's webhook endpoints."""

    def create(
        self,
        *,
        url: str,
        secret: str,
        events: Sequence[str] | None = None,
        company: str | None = None,
    ) -> dict:
        """Registers an HTTPS endpoint for this company's events.

        `secret` (16 to 255 characters) signs every delivery; it is never
        returned again, so keep it. `events` narrows what is sent, from
        EVENTS; left out, the endpoint receives every event. The API
        refuses a URL that is not HTTPS or points at a private network.
        """
        if not url.lower().startswith("https://"):
            raise ValueError("url must be an https:// URL")
        if len(url) > _URL_MAX:
            raise ValueError(f"url must be at most {_URL_MAX} characters")
        if not _SECRET_MIN <= len(secret) <= _SECRET_MAX:
            raise ValueError(
                f"secret must be {_SECRET_MIN} to {_SECRET_MAX} characters"
            )

        payload: dict[str, Any] = {"url": url, "secret": secret}
        if events is not None:
            if isinstance(events, str):
                raise ValueError("events must be a list of event names")
            unknown = sorted(set(events) - set(EVENTS))
            if unknown:
                raise ValueError(
                    f"unknown events: {', '.join(unknown)}. "
                    f"Known: {', '.join(EVENTS)}"
                )
            payload["events"] = list(events)

        return cast(
            dict,
            self._request("POST", "/webhooks", json=payload, company=company),
        )

    def list(self, *, company: str | None = None) -> list:
        """This company's endpoints in the credential's environment.

        A plain list, not a page. Secrets are never returned.
        """
        return cast(list, self._request("GET", "/webhooks", company=company))

    def delete(self, endpoint_id: str, *, company: str | None = None) -> None:
        """Stops delivery to one endpoint, keeping what was already sent.

        An id this company does not have is an APIError 404.
        """
        self._request("DELETE", f"/webhooks/{_segment(endpoint_id)}", company=company)

    def deliveries(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
        sort_by: str | None = None,
        order_by: str | None = None,
        company: str | None = None,
    ) -> dict:
        """Every delivery attempt in the credential's environment, a page.

        Each row has the `event`, its `status`, `attempts`, the
        endpoint's `response_status`, `last_error` and when it was
        delivered or will be tried again.
        """
        return cast(
            dict,
            self._request(
                "GET",
                "/webhooks/deliveries",
                params=_page_params(limit, offset, sort_by, order_by),
                company=company,
            ),
        )
