"""
audit.providers - Provider package for crash-report portal connectors.
"""

from .base import BaseProvider
from .socrata import SocrataProvider
from .legacy_portal import LegacyPortalProvider

__all__ = ["BaseProvider", "SocrataProvider", "LegacyPortalProvider"]
