#!/usr/bin/env python3
"""
run_audit.py - Entry point for the crash-portal PII exposure assessment.

Usage
-----
    python run_audit.py [OPTIONS]

Options
-------
--provider   Provider to scan: "legacy" (default) or "socrata"
--output     Path to write the JSON report (default: reports/audit_report.json)
--no-file    Skip writing the JSON report to disk
--quiet      Suppress the human-readable summary printed to stdout
--app-token  Socrata application token (only used with --provider=socrata)

Examples
--------
    # Scan the simulated legacy portal and write report to default location
    python run_audit.py

    # Scan the live Socrata API (requires network access)
    python run_audit.py --provider socrata --app-token YOUR_TOKEN

    # Write report to a custom path
    python run_audit.py --output /tmp/my_report.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from audit import ExposureScanner, ReportingLayer
from audit.providers import LegacyPortalProvider, SocrataProvider


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="run_audit",
        description="PII Exposure Assessment — Crash-Report Portal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--provider",
        choices=["legacy", "socrata"],
        default="legacy",
        help="Provider to scan (default: legacy)",
    )
    parser.add_argument(
        "--output",
        default="reports/audit_report.json",
        help="Output path for the JSON report (default: reports/audit_report.json)",
    )
    parser.add_argument(
        "--no-file",
        action="store_true",
        help="Skip writing the JSON report to disk",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the human-readable summary",
    )
    parser.add_argument(
        "--app-token",
        default=None,
        help="Socrata application token (only used with --provider=socrata)",
    )
    return parser.parse_args(argv)


def build_provider(args: argparse.Namespace):
    if args.provider == "socrata":
        return SocrataProvider(app_token=args.app_token)
    return LegacyPortalProvider()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    provider = build_provider(args)
    scanner = ExposureScanner(provider)

    print(f"[*] Starting assessment against: {provider.name}")
    print(f"[*] Access state: pre-authentication\n")

    result = scanner.run()

    output_path = None if args.no_file else Path(args.output)
    reporter = ReportingLayer(output_path=output_path)

    json_report = reporter.generate(result)

    if not args.quiet:
        reporter.print_summary(result)

    if output_path:
        print(f"[*] JSON report written to: {output_path}")

    # Exit code: 0 if no critical/high findings, 1 otherwise
    high_severity_found = any(
        f.severity in ("CRITICAL", "HIGH") for f in result.findings
    )
    return 1 if high_severity_found else 0


if __name__ == "__main__":
    sys.exit(main())
