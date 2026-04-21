"""
legacy_portal.py - LegacyPortalProvider: simulates a weakly protected legacy
crash-report portal that exposes PII in a pre-authentication state.

This provider is used **exclusively** for security assessment purposes on
authorised engagements.  It does NOT make real network requests; instead it
returns synthetic response fixtures that mirror common misconfigurations
observed in legacy law-enforcement / insurance crash-report portals.

Simulated weaknesses
--------------------
* Crash-detail endpoint returns full names and phone numbers without tokens.
* Insurance lookup endpoint returns policy numbers in the query response.
* Driver-history endpoint exposes date-of-birth and driver licence numbers.
* Search endpoint leaks e-mail addresses in autocomplete suggestions.
"""

from __future__ import annotations

import urllib.parse
from typing import Any

from .base import BaseProvider


# ---------------------------------------------------------------------------
# Fixture data — realistic but entirely synthetic PII
# ---------------------------------------------------------------------------

_FIXTURES: dict[str, Any] = {
    "/api/crashes/detail": [
        {
            "crash_id": "CHI-2023-001",
            "report_date": "2023-06-15",
            "location": "N Michigan Ave & E Grand Ave",
            "officer_name": "James Carter",
            "involved_parties": [
                {
                    "name": "Alice Johnson",
                    "phone": "312-555-0147",
                    "email": "alice.johnson@example.com",
                    "role": "driver",
                },
                {
                    "name": "Robert Smith",
                    "phone": "773-555-0293",
                    "email": "r.smith@example.net",
                    "role": "passenger",
                },
            ],
        }
    ],
    "/api/crashes/insurance-lookup": [
        {
            "crash_id": "CHI-2023-001",
            "insurance_id": "GEICO-1048273",
            "policy_number": "PL9948271-A",
            "provider": "GEICO",
            "claimant": "Alice Johnson",
            "status": "open",
        }
    ],
    "/api/crashes/driver-history": [
        {
            "name": "Alice Johnson",
            "dob": "1985-03-22",
            "dl_number": "A9284710",
            "license_state": "IL",
            "violation_count": 2,
        }
    ],
    "/api/crashes/search-suggest": {
        "query": "ali",
        "suggestions": [
            "alice.johnson@example.com",
            "alicia.rivera@example.org",
        ],
    },
    "/api/crashes/report-export": (
        "CRASH REPORT — CHI-2023-001\n"
        "Driver: Alice Johnson\n"
        "DOB: 1985-03-22\n"
        "SSN: 123-45-6789\n"
        "Phone: 312-555-0147\n"
        "Insurance ID: GEICO-1048273\n"
    ),
}


class LegacyPortalProvider(BaseProvider):
    """
    Simulated legacy crash-report portal provider for security assessment.

    Parameters
    ----------
    base_url:
        Conceptual base URL of the legacy portal under assessment.
        Defaults to ``"https://legacy-crashportal.example.gov"``.
    """

    def __init__(
        self,
        base_url: str = "https://legacy-crashportal.example.gov",
    ) -> None:
        self._base_url = base_url.rstrip("/")

    # ------------------------------------------------------------------
    # BaseProvider interface
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return "Legacy Crash-Report Portal (simulated)"

    def get_endpoints(self) -> list[dict[str, Any]]:
        return [
            {
                "url": f"{self._base_url}/api/crashes/detail",
                "description": "Crash detail — returns full party names and contact info",
                "requires_auth": False,  # misconfiguration: should require auth
            },
            {
                "url": f"{self._base_url}/api/crashes/insurance-lookup",
                "description": "Insurance lookup — exposes policy numbers pre-auth",
                "requires_auth": False,
            },
            {
                "url": f"{self._base_url}/api/crashes/driver-history",
                "description": "Driver history — exposes DOB and licence numbers",
                "requires_auth": False,
            },
            {
                "url": f"{self._base_url}/api/crashes/search-suggest",
                "description": "Autocomplete search — leaks e-mail addresses",
                "requires_auth": False,
            },
            {
                "url": f"{self._base_url}/api/crashes/report-export",
                "description": "Report export — plaintext with SSN and PII",
                "requires_auth": False,
            },
        ]

    def fetch(self, endpoint: str) -> Any:
        """Return synthetic fixture data for *endpoint*.

        This method never makes real network requests.  It looks up the
        path portion of *endpoint* in the fixture registry and returns the
        corresponding synthetic payload.

        Raises
        ------
        KeyError
            If *endpoint* is not in the fixture registry.
        """
        path = self._extract_path(endpoint)
        if path not in _FIXTURES:
            raise KeyError(
                f"No fixture registered for endpoint path '{path}'. "
                "Available paths: " + ", ".join(_FIXTURES.keys())
            )
        return _FIXTURES[path]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_path(url: str) -> str:
        """Extract the path component from a full URL."""
        parsed = urllib.parse.urlparse(url)
        return parsed.path
