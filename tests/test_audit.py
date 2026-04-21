"""
tests/test_audit.py - Unit tests for the audit package.
"""

import json
import io
import sys
import os

# Ensure repo root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from audit.scanner import ExposureScanner, Finding, ScanResult
from audit.reporting import ReportingLayer
from audit.providers.legacy_portal import LegacyPortalProvider
from audit.providers.socrata import SocrataProvider
from audit.providers.base import BaseProvider


# ---------------------------------------------------------------------------
# Minimal stub provider for unit tests
# ---------------------------------------------------------------------------

class StubProvider(BaseProvider):
    """Provider that returns controlled test data."""

    def __init__(self, responses: dict):
        self._responses = responses  # {url: payload}

    @property
    def name(self) -> str:
        return "Stub Provider"

    def get_endpoints(self):
        return [{"url": url, "description": "", "requires_auth": False}
                for url in self._responses]

    def fetch(self, endpoint: str):
        return self._responses[endpoint]


# ---------------------------------------------------------------------------
# ExposureScanner tests
# ---------------------------------------------------------------------------

class TestExposureScanner:

    def test_detects_email_in_response(self):
        provider = StubProvider({
            "http://example.com/api": {"contact": "test@example.com"}
        })
        scanner = ExposureScanner(provider)
        result = scanner.run()
        fields = {f.field_detected for f in result.findings}
        assert "email" in fields

    def test_detects_phone_number(self):
        provider = StubProvider({
            "http://example.com/api": {"phone": "312-555-0147"}
        })
        scanner = ExposureScanner(provider)
        result = scanner.run()
        fields = {f.field_detected for f in result.findings}
        assert "phone_number" in fields

    def test_detects_ssn(self):
        provider = StubProvider({
            "http://example.com/api": "SSN: 123-45-6789"
        })
        scanner = ExposureScanner(provider)
        result = scanner.run()
        fields = {f.field_detected for f in result.findings}
        assert "ssn" in fields

    def test_detects_insurance_id_from_key(self):
        provider = StubProvider({
            "http://example.com/api": {"insurance_id": "GEICO-1048273"}
        })
        scanner = ExposureScanner(provider)
        result = scanner.run()
        fields = {f.field_detected for f in result.findings}
        assert "insurance_id" in fields

    def test_detects_full_name(self):
        provider = StubProvider({
            "http://example.com/api": {"name": "Alice Johnson"}
        })
        scanner = ExposureScanner(provider)
        result = scanner.run()
        fields = {f.field_detected for f in result.findings}
        assert "full_name" in fields

    def test_severity_critical_for_ssn(self):
        provider = StubProvider({
            "http://example.com/api": "SSN: 123-45-6789"
        })
        scanner = ExposureScanner(provider)
        result = scanner.run()
        ssn_findings = [f for f in result.findings if f.field_detected == "ssn"]
        assert ssn_findings
        assert ssn_findings[0].severity == "CRITICAL"

    def test_severity_medium_for_email(self):
        provider = StubProvider({
            "http://example.com/api": {"email": "user@example.com"}
        })
        scanner = ExposureScanner(provider)
        result = scanner.run()
        email_findings = [f for f in result.findings if f.field_detected == "email"]
        assert email_findings
        assert email_findings[0].severity == "MEDIUM"

    def test_access_state_default(self):
        provider = StubProvider({
            "http://example.com/api": {"email": "user@example.com"}
        })
        scanner = ExposureScanner(provider)
        result = scanner.run()
        assert all(f.access_state == "pre-authentication" for f in result.findings)

    def test_access_state_custom(self):
        provider = StubProvider({
            "http://example.com/api": {"email": "user@example.com"}
        })
        scanner = ExposureScanner(provider, access_state="post-authentication")
        result = scanner.run()
        assert all(f.access_state == "post-authentication" for f in result.findings)

    def test_no_findings_for_clean_data(self):
        provider = StubProvider({
            "http://example.com/api": {"crash_id": "CHI-001", "severity": "minor"}
        })
        scanner = ExposureScanner(provider)
        result = scanner.run()
        assert result.findings == []

    def test_error_handling_for_failing_fetch(self):
        class FailingProvider(BaseProvider):
            @property
            def name(self): return "Failing"
            def get_endpoints(self):
                return [{"url": "http://fail.example.com/api", "description": "", "requires_auth": False}]
            def fetch(self, endpoint):
                raise ConnectionError("Network unreachable")

        scanner = ExposureScanner(FailingProvider())
        result = scanner.run()
        assert result.findings == []
        assert len(result.errors) == 1
        assert "Network unreachable" in result.errors[0]["error"]

    def test_endpoint_tracked(self):
        url = "http://example.com/api"
        provider = StubProvider({url: {}})
        scanner = ExposureScanner(provider)
        result = scanner.run()
        assert url in result.scanned_endpoints


# ---------------------------------------------------------------------------
# ReportingLayer tests
# ---------------------------------------------------------------------------

class TestReportingLayer:

    def _make_result(self, findings=None):
        result = ScanResult(provider_name="Test Provider")
        result.findings = findings or []
        result.scanned_endpoints = ["http://example.com/api"]
        return result

    def test_generate_returns_valid_json(self):
        result = self._make_result([
            Finding(
                field_detected="email",
                endpoint="http://example.com/api",
                access_state="pre-authentication",
                severity="MEDIUM",
            )
        ])
        reporter = ReportingLayer()
        json_str = reporter.generate(result)
        data = json.loads(json_str)
        assert "findings" in data
        assert "report_metadata" in data

    def test_finding_fields_in_output(self):
        finding = Finding(
            field_detected="ssn",
            endpoint="http://example.com/api/report",
            access_state="pre-authentication",
            severity="CRITICAL",
        )
        result = self._make_result([finding])
        reporter = ReportingLayer()
        json_str = reporter.generate(result)
        data = json.loads(json_str)
        f = data["findings"][0]
        assert f["field_detected"] == "ssn"
        assert f["endpoint"] == "http://example.com/api/report"
        assert f["access_state"] == "pre-authentication"
        assert f["severity"] == "CRITICAL"

    def test_metadata_counts(self):
        findings = [
            Finding("email", "http://example.com/1", "pre-authentication", "MEDIUM"),
            Finding("ssn",   "http://example.com/2", "pre-authentication", "CRITICAL"),
        ]
        result = self._make_result(findings)
        reporter = ReportingLayer()
        data = json.loads(reporter.generate(result))
        assert data["report_metadata"]["total_findings"] == 2

    def test_writes_to_stream(self):
        result = self._make_result()
        buf = io.StringIO()
        reporter = ReportingLayer(stream=buf)
        reporter.generate(result)
        assert len(buf.getvalue()) > 0

    def test_writes_to_file(self, tmp_path):
        result = self._make_result()
        out_file = tmp_path / "report.json"
        reporter = ReportingLayer(output_path=out_file)
        reporter.generate(result)
        assert out_file.exists()
        data = json.loads(out_file.read_text())
        assert "findings" in data

    def test_print_summary_no_crash(self):
        result = self._make_result()
        buf = io.StringIO()
        reporter = ReportingLayer()
        reporter.print_summary(result, stream=buf)
        output = buf.getvalue()
        assert "SECURITY ASSESSMENT REPORT" in output


# ---------------------------------------------------------------------------
# LegacyPortalProvider tests
# ---------------------------------------------------------------------------

class TestLegacyPortalProvider:

    def test_name(self):
        p = LegacyPortalProvider()
        assert "Legacy" in p.name

    def test_get_endpoints_returns_list(self):
        p = LegacyPortalProvider()
        endpoints = p.get_endpoints()
        assert isinstance(endpoints, list)
        assert len(endpoints) > 0

    def test_endpoints_have_required_keys(self):
        p = LegacyPortalProvider()
        for ep in p.get_endpoints():
            assert "url" in ep
            assert "description" in ep
            assert "requires_auth" in ep

    def test_fetch_detail_endpoint(self):
        p = LegacyPortalProvider()
        data = p.fetch("https://legacy-crashportal.example.gov/api/crashes/detail")
        assert isinstance(data, list)
        assert len(data) > 0

    def test_fetch_unknown_endpoint_raises(self):
        p = LegacyPortalProvider()
        with pytest.raises(KeyError):
            p.fetch("https://legacy-crashportal.example.gov/api/unknown")

    def test_is_not_authenticated(self):
        p = LegacyPortalProvider()
        assert p.is_authenticated() is False

    def test_scan_finds_critical_ssn(self):
        p = LegacyPortalProvider()
        scanner = ExposureScanner(p)
        result = scanner.run()
        critical = [f for f in result.findings if f.severity == "CRITICAL"]
        assert len(critical) > 0, "Expected at least one CRITICAL finding (SSN)"

    def test_scan_finds_high_insurance(self):
        p = LegacyPortalProvider()
        scanner = ExposureScanner(p)
        result = scanner.run()
        fields = {f.field_detected for f in result.findings}
        assert "insurance_id" in fields


# ---------------------------------------------------------------------------
# Integration: run_audit entry point
# ---------------------------------------------------------------------------

class TestRunAudit:

    def test_main_legacy_no_file(self):
        from run_audit import main
        exit_code = main(["--provider", "legacy", "--no-file", "--quiet"])
        assert exit_code in (0, 1)

    def test_main_returns_1_for_critical_findings(self):
        from run_audit import main
        # Legacy provider always has CRITICAL findings
        exit_code = main(["--provider", "legacy", "--no-file", "--quiet"])
        assert exit_code == 1
