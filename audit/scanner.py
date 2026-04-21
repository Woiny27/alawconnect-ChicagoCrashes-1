"""
scanner.py - ExposureScanner: detects PII fields in endpoint responses
obtained in a pre-authentication state.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# PII detection patterns
# ---------------------------------------------------------------------------

_PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "email": re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"),
    "phone_number": re.compile(
        r"(\+?1[\s\-.]?)?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}"
    ),
    "full_name": re.compile(
        r"\b([A-Z][a-z]+\s[A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\b"
    ),
    "insurance_id": re.compile(
        r"\b([A-Z]{2,4}[\s\-]?\d{6,12}|[A-Z]\d{7,})\b"
    ),
    "ssn": re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b"),
    "date_of_birth": re.compile(
        r"\b(dob|date_of_birth|birthdate)\b", re.IGNORECASE
    ),
    "drivers_license": re.compile(
        r"\b(dl_number|driver_license|drivers_license|license_number)\b",
        re.IGNORECASE,
    ),
}

# Severity mapping: higher sensitivity → higher severity
_FIELD_SEVERITY: dict[str, str] = {
    "ssn": "CRITICAL",
    "insurance_id": "HIGH",
    "drivers_license": "HIGH",
    "date_of_birth": "HIGH",
    "email": "MEDIUM",
    "phone_number": "MEDIUM",
    "full_name": "LOW",
}


@dataclass
class Finding:
    """Represents a single PII exposure finding."""

    field_detected: str
    endpoint: str
    access_state: str
    severity: str
    sample_match: str = ""


@dataclass
class ScanResult:
    """Aggregated results from scanning a set of endpoints."""

    provider_name: str
    findings: list[Finding] = field(default_factory=list)
    scanned_endpoints: list[str] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)


class ExposureScanner:
    """
    Inspects provider endpoints for PII accessible in a pre-authentication
    state and produces a structured list of :class:`Finding` objects.

    Parameters
    ----------
    provider:
        A provider instance that implements ``BaseProvider`` and supplies
        the endpoints and raw response data to be evaluated.
    access_state:
        Label describing the authentication level under which the scan
        is performed (default: ``"pre-authentication"``).
    """

    def __init__(self, provider: Any, access_state: str = "pre-authentication") -> None:
        self.provider = provider
        self.access_state = access_state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> ScanResult:
        """Execute the scan across all provider endpoints.

        Returns
        -------
        ScanResult
            Aggregated scan results containing all findings and metadata.
        """
        result = ScanResult(provider_name=self.provider.name)

        for endpoint_meta in self.provider.get_endpoints():
            endpoint = endpoint_meta["url"]
            result.scanned_endpoints.append(endpoint)

            try:
                data = self.provider.fetch(endpoint)
                findings = self._inspect(data, endpoint)
                result.findings.extend(findings)
            except Exception as exc:  # noqa: BLE001
                result.errors.append({"endpoint": endpoint, "error": str(exc)})

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _inspect(self, data: Any, endpoint: str) -> list[Finding]:
        """Scan *data* (dict, list, or str) for PII patterns."""
        text = self._to_text(data)
        findings: list[Finding] = []

        for field_name, pattern in _PII_PATTERNS.items():
            match = pattern.search(text)
            if match:
                sample = self._redact(match.group(0))
                findings.append(
                    Finding(
                        field_detected=field_name,
                        endpoint=endpoint,
                        access_state=self.access_state,
                        severity=_FIELD_SEVERITY.get(field_name, "LOW"),
                        sample_match=sample,
                    )
                )

        # Also inspect dict keys for sensitive field names
        if isinstance(data, (dict, list)):
            key_findings = self._inspect_keys(data, endpoint)
            # Avoid duplicating findings already detected via value scanning
            existing_fields = {f.field_detected for f in findings}
            for kf in key_findings:
                if kf.field_detected not in existing_fields:
                    findings.append(kf)

        return findings

    def _inspect_keys(self, data: Any, endpoint: str) -> list[Finding]:
        """Detect sensitive field names in dict keys / JSON keys."""
        keys = self._collect_keys(data)
        findings: list[Finding] = []

        sensitive_key_patterns: dict[str, tuple[str, re.Pattern[str]]] = {
            "full_name": (
                "LOW",
                re.compile(r"\b(name|full_name|first_name|last_name)\b", re.IGNORECASE),
            ),
            "phone_number": (
                "MEDIUM",
                re.compile(r"\b(phone|phone_number|mobile|cell)\b", re.IGNORECASE),
            ),
            "email": (
                "MEDIUM",
                re.compile(r"\b(email|e_mail|email_address)\b", re.IGNORECASE),
            ),
            "insurance_id": (
                "HIGH",
                re.compile(
                    r"\b(insurance|insurance_id|policy|policy_number)\b",
                    re.IGNORECASE,
                ),
            ),
            "ssn": (
                "CRITICAL",
                re.compile(r"\b(ssn|social_security|tax_id)\b", re.IGNORECASE),
            ),
            "drivers_license": (
                "HIGH",
                re.compile(
                    r"\b(dl_number|driver_license|drivers_license|license_number)\b",
                    re.IGNORECASE,
                ),
            ),
            "date_of_birth": (
                "HIGH",
                re.compile(
                    r"\b(dob|date_of_birth|birthdate|birth_date)\b", re.IGNORECASE
                ),
            ),
        }

        for key in keys:
            for field_name, (severity, pattern) in sensitive_key_patterns.items():
                if pattern.search(key):
                    findings.append(
                        Finding(
                            field_detected=field_name,
                            endpoint=endpoint,
                            access_state=self.access_state,
                            severity=severity,
                            sample_match=f"[key: {key}]",
                        )
                    )
                    break  # one finding per key

        return findings

    @staticmethod
    def _collect_keys(data: Any, max_depth: int = 5) -> list[str]:
        """Recursively collect all dict keys up to *max_depth* levels."""
        keys: list[str] = []

        def _recurse(obj: Any, depth: int) -> None:
            if depth > max_depth:
                return
            if isinstance(obj, dict):
                for k, v in obj.items():
                    keys.append(str(k))
                    _recurse(v, depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    _recurse(item, depth + 1)

        _recurse(data, 0)
        return keys

    @staticmethod
    def _to_text(data: Any) -> str:
        """Flatten *data* to a plain string for regex scanning."""
        if isinstance(data, str):
            return data
        if isinstance(data, (dict, list)):
            return json.dumps(data)
        return str(data)

    @staticmethod
    def _redact(value: str) -> str:
        """Return a partially redacted version of *value* for safe logging."""
        if len(value) <= 4:
            return "****"
        visible = max(2, len(value) // 4)
        return value[:visible] + "*" * (len(value) - visible)
