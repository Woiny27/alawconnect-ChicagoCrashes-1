"""
reporting.py - ReportingLayer: serialises ExposureScanner findings to JSON.

Output schema per finding
-------------------------
{
    "field_detected": "<pii_type>",
    "endpoint":       "<url>",
    "access_state":   "<authentication_level>",
    "severity":       "<CRITICAL|HIGH|MEDIUM|LOW>"
}
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import IO, Any

from .scanner import Finding, ScanResult


class ReportingLayer:
    """
    Converts :class:`~audit.scanner.ScanResult` data into a structured JSON
    report and writes it to a file path or an output stream.

    Parameters
    ----------
    output_path:
        Optional file path.  When provided, the JSON report is written to
        that file in addition to (or instead of) being returned as a string.
    stream:
        Optional writable stream (e.g. ``sys.stdout``).  When provided,
        the report is also written to the stream.
    indent:
        JSON indentation level (default: 2).
    """

    def __init__(
        self,
        output_path: str | Path | None = None,
        stream: IO[str] | None = None,
        indent: int = 2,
    ) -> None:
        self.output_path = Path(output_path) if output_path else None
        self.stream = stream
        self.indent = indent

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, result: ScanResult) -> str:
        """Serialise *result* and write / return the JSON report.

        Parameters
        ----------
        result:
            The :class:`~audit.scanner.ScanResult` to report on.

        Returns
        -------
        str
            The JSON-encoded report string.
        """
        report = self._build_report(result)
        json_str = json.dumps(report, indent=self.indent)

        if self.output_path:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            self.output_path.write_text(json_str, encoding="utf-8")

        if self.stream:
            self.stream.write(json_str)
            self.stream.write("\n")

        return json_str

    def print_summary(self, result: ScanResult, stream: IO[str] | None = None) -> None:
        """Print a human-readable summary to *stream* (default: stdout)."""
        out = stream or sys.stdout
        divider = "=" * 60
        out.write(f"\n{divider}\n")
        out.write(f"  SECURITY ASSESSMENT REPORT — {result.provider_name}\n")
        out.write(f"{divider}\n")
        out.write(
            f"  Scanned at : {datetime.now(timezone.utc).isoformat()}\n"
        )
        out.write(f"  Endpoints  : {len(result.scanned_endpoints)}\n")
        out.write(f"  Findings   : {len(result.findings)}\n")
        out.write(f"  Errors     : {len(result.errors)}\n")
        out.write(f"{divider}\n\n")

        if not result.findings:
            out.write("  No PII exposure detected.\n\n")
            return

        # Group findings by severity for display
        severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        grouped: dict[str, list[Finding]] = {s: [] for s in severity_order}
        for finding in result.findings:
            grouped.setdefault(finding.severity, []).append(finding)

        for severity in severity_order:
            items = grouped.get(severity, [])
            if not items:
                continue
            out.write(f"  [{severity}]\n")
            for item in items:
                out.write(f"    field     : {item.field_detected}\n")
                out.write(f"    endpoint  : {item.endpoint}\n")
                out.write(f"    access    : {item.access_state}\n")
                if item.sample_match:
                    out.write(f"    sample    : {item.sample_match}\n")
                out.write("\n")

        if result.errors:
            out.write("  [ERRORS]\n")
            for err in result.errors:
                out.write(f"    {err['endpoint']}: {err['error']}\n")
            out.write("\n")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_report(self, result: ScanResult) -> dict[str, Any]:
        return {
            "report_metadata": {
                "provider": result.provider_name,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_endpoints_scanned": len(result.scanned_endpoints),
                "total_findings": len(result.findings),
                "total_errors": len(result.errors),
            },
            "findings": [self._serialise_finding(f) for f in result.findings],
            "errors": result.errors,
        }

    @staticmethod
    def _serialise_finding(finding: Finding) -> dict[str, str]:
        return {
            "field_detected": finding.field_detected,
            "endpoint": finding.endpoint,
            "access_state": finding.access_state,
            "severity": finding.severity,
        }
