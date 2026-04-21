# alawconnect-ChicagoCrashes-1

## Security Assessment Prototype — Crash-Report Portal PII Exposure Scanner

This repository contains a Python-based security assessment prototype for an
**authorised** crash-report portal engagement.  It scans portal endpoints for
personally identifiable information (PII) that is accessible without
authentication and produces a structured JSON report with remediation guidance.

> ⚠️ **Authorised use only.**  This tool must only be run against portals for
> which you have explicit written permission.  Unauthorised scanning may violate
> computer-fraud laws.

---

## Project Structure

```
.
├── audit/                        # Core assessment package
│   ├── __init__.py
│   ├── scanner.py                # ExposureScanner — detects PII in responses
│   ├── reporting.py              # ReportingLayer  — outputs structured JSON
│   └── providers/
│       ├── __init__.py
│       ├── base.py               # Abstract BaseProvider
│       ├── socrata.py            # SocrataProvider (City of Chicago open data)
│       └── legacy_portal.py     # LegacyPortalProvider (simulated weak portal)
├── reports/                      # Generated audit reports (git-ignored)
├── run_audit.py                  # CLI entry point
├── remediation_report_template.md
└── README.md
```

---

## Requirements

- Python 3.9 or later
- No third-party dependencies — the standard library is sufficient.

---

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/Woiny27/alawconnect-ChicagoCrashes-1.git
cd alawconnect-ChicagoCrashes-1

# 2. (Optional) Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Verify Python version
python --version             # should be 3.9+
```

No `pip install` step is required — the tool uses only built-in modules.

---

## Running the Assessment

### Simulated legacy portal (default — no network access required)

```bash
python run_audit.py
```

This scans the built-in `LegacyPortalProvider` fixtures and writes the report
to `reports/audit_report.json`.

### Live Socrata / City of Chicago API

```bash
python run_audit.py --provider socrata
```

Optionally supply a Socrata application token to increase rate limits:

```bash
python run_audit.py --provider socrata --app-token YOUR_APP_TOKEN
```

### Additional options

| Flag | Description |
|------|-------------|
| `--output PATH` | Custom path for the JSON report (default: `reports/audit_report.json`) |
| `--no-file` | Skip writing the report to disk |
| `--quiet` | Suppress the human-readable summary on stdout |
| `--provider {legacy,socrata}` | Select the provider to scan |

### Exit codes

| Code | Meaning |
|------|---------|
| `0`  | No CRITICAL or HIGH severity findings |
| `1`  | At least one CRITICAL or HIGH severity finding detected |

---

## JSON Report Format

Each finding in the output report follows this schema:

```json
{
  "field_detected": "<pii_type>",
  "endpoint":       "<url>",
  "access_state":   "<authentication_level>",
  "severity":       "<CRITICAL|HIGH|MEDIUM|LOW>"
}
```

The full report also includes metadata (provider name, timestamp, totals) and
an errors section for any endpoints that could not be reached.

**Example output:**

```json
{
  "report_metadata": {
    "provider": "Legacy Crash-Report Portal (simulated)",
    "generated_at": "2024-01-15T10:30:00+00:00",
    "total_endpoints_scanned": 5,
    "total_findings": 8,
    "total_errors": 0
  },
  "findings": [
    {
      "field_detected": "ssn",
      "endpoint": "https://legacy-crashportal.example.gov/api/crashes/report-export",
      "access_state": "pre-authentication",
      "severity": "CRITICAL"
    },
    {
      "field_detected": "insurance_id",
      "endpoint": "https://legacy-crashportal.example.gov/api/crashes/insurance-lookup",
      "access_state": "pre-authentication",
      "severity": "HIGH"
    }
  ],
  "errors": []
}
```

---

## Severity Levels

| Severity | PII Types |
|----------|-----------|
| CRITICAL | Social Security Numbers (SSN) |
| HIGH     | Insurance IDs, Driver licence numbers, Date of birth |
| MEDIUM   | Email addresses, Phone numbers |
| LOW      | Full names |

---

## Remediation

See [`remediation_report_template.md`](remediation_report_template.md) for a
ready-to-use client-facing remediation report template.

---

## Extending the Tool

### Adding a new provider

1. Create a new file in `audit/providers/`, e.g. `my_portal.py`.
2. Subclass `BaseProvider` and implement `name`, `get_endpoints()`, and `fetch()`.
3. Import and register it in `audit/providers/__init__.py`.
4. Add a `--provider` choice in `run_audit.py`.

### Adjusting PII patterns

Edit the `_PII_PATTERNS` and `_FIELD_SEVERITY` dictionaries in
`audit/scanner.py` to add or tune detection rules.

---

## Running Tests

```bash
python -m pytest tests/ -v
```
