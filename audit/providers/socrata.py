"""
socrata.py - SocrataProvider: connector for the City of Chicago open data
portal (Socrata API) covering traffic-crash datasets.

The provider operates in a **read-only, unauthenticated** mode by default,
which is intentional for pre-authentication exposure assessment.  An optional
``app_token`` may be supplied to raise API rate limits without granting any
additional data access.

Relevant Chicago datasets
--------------------------
- Crashes   : https://data.cityofchicago.org/resource/85ca-t3if.json
- People    : https://data.cityofchicago.org/resource/u6pd-qa9d.json
- Vehicles  : https://data.cityofchicago.org/resource/68nd-jvt3.json
"""

from __future__ import annotations

import urllib.request
import urllib.parse
import json
from typing import Any

from .base import BaseProvider


class SocrataProvider(BaseProvider):
    """
    Provider for the City of Chicago Socrata open-data API.

    Parameters
    ----------
    base_url:
        Root URL of the Socrata instance
        (default: ``"https://data.cityofchicago.org"``).
    app_token:
        Optional Socrata application token.  Increases rate limits but does
        not bypass row-level access controls.
    row_limit:
        Number of rows to retrieve per endpoint for sampling
        (default: 5).
    timeout:
        HTTP request timeout in seconds (default: 15).
    """

    _DEFAULT_BASE_URL = "https://data.cityofchicago.org"

    _DATASETS: list[dict[str, Any]] = [
        {
            "dataset_id": "85ca-t3if",
            "description": "Traffic Crashes – Crash-level records",
            "requires_auth": False,
        },
        {
            "dataset_id": "u6pd-qa9d",
            "description": "Traffic Crashes – People involved",
            "requires_auth": False,
        },
        {
            "dataset_id": "68nd-jvt3",
            "description": "Traffic Crashes – Vehicles involved",
            "requires_auth": False,
        },
    ]

    def __init__(
        self,
        base_url: str = _DEFAULT_BASE_URL,
        app_token: str | None = None,
        row_limit: int = 5,
        timeout: int = 15,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._app_token = app_token
        self._row_limit = row_limit
        self._timeout = timeout

    # ------------------------------------------------------------------
    # BaseProvider interface
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return "City of Chicago – Socrata Open Data API"

    def get_endpoints(self) -> list[dict[str, Any]]:
        endpoints = []
        for ds in self._DATASETS:
            url = self._build_url(ds["dataset_id"])
            endpoints.append(
                {
                    "url": url,
                    "description": ds["description"],
                    "requires_auth": ds["requires_auth"],
                }
            )
        return endpoints

    def fetch(self, endpoint: str) -> Any:
        """Retrieve a sample of rows from *endpoint* as a Python list."""
        req = urllib.request.Request(endpoint)
        if self._app_token:
            req.add_header("X-App-Token", self._app_token)
        req.add_header("Accept", "application/json")

        with urllib.request.urlopen(req, timeout=self._timeout) as resp:  # noqa: S310
            raw = resp.read().decode("utf-8")

        return json.loads(raw)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_url(self, dataset_id: str) -> str:
        params = urllib.parse.urlencode({"$limit": self._row_limit})
        return f"{self._base_url}/resource/{dataset_id}.json?{params}"
