"""
base.py - Abstract base class for all data / portal providers.

Every provider must implement:
  - ``name``  (str property) — human-readable provider identifier.
  - ``get_endpoints()`` — returns a list of endpoint metadata dicts.
  - ``fetch(endpoint)``  — retrieves data from a single endpoint and returns
    it as a Python object (dict, list, or str).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    """Abstract base class for crash-report portal providers."""

    # ------------------------------------------------------------------
    # Required interface
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider identifier."""

    @abstractmethod
    def get_endpoints(self) -> list[dict[str, Any]]:
        """Return a list of endpoint descriptors.

        Each descriptor is a dict with at least::

            {
                "url": "<full endpoint URL>",
                "description": "<human-readable description>",
                "requires_auth": <bool>
            }
        """

    @abstractmethod
    def fetch(self, endpoint: str) -> Any:
        """Fetch and return data from *endpoint*.

        Returns the response payload as a Python dict, list, or string.
        Implementations should raise an exception on network or HTTP errors.
        """

    # ------------------------------------------------------------------
    # Optional helpers (may be overridden)
    # ------------------------------------------------------------------

    def is_authenticated(self) -> bool:
        """Return ``True`` if the provider currently holds valid credentials."""
        return False
