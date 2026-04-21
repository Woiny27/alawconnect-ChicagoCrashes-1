# Remediation Report Template

**Assessment Reference:** `[ENGAGEMENT_ID]`  
**Client:** `[CLIENT_NAME]`  
**Portal / System:** `[PORTAL_NAME / URL]`  
**Assessment Date:** `[DATE]`  
**Prepared by:** `[ASSESSOR_NAME / FIRM]`  
**Classification:** CONFIDENTIAL

---

## Executive Summary

During a pre-authentication security assessment of **[PORTAL_NAME]**, the
assessment team identified **[N]** endpoints that expose personally
identifiable information (PII) without requiring any form of user
authentication.  The data exposed includes [list types, e.g. full names,
email addresses, insurance policy numbers, and driver-licence numbers].

Exploitation of these weaknesses by an unauthorised actor could result in
identity theft, insurance fraud, regulatory penalties under applicable privacy
laws (e.g., CCPA, HIPAA, DPPA), and significant reputational harm.

**Overall Risk Rating:** `[CRITICAL / HIGH / MEDIUM / LOW]`

---

## Scope

| Item | Value |
|------|-------|
| Portal URL | `[URL]` |
| Assessment type | Black-box, pre-authentication |
| Assessment tool | alawconnect-ChicagoCrashes-1 ExposureScanner |
| Endpoints scanned | `[N]` |
| Findings | `[N]` |

---

## Findings Summary

| # | Endpoint | PII Exposed | Severity |
|---|----------|-------------|----------|
| 1 | `/api/crashes/report-export` | SSN | CRITICAL |
| 2 | `/api/crashes/insurance-lookup` | Insurance ID, Policy Number | HIGH |
| 3 | `/api/crashes/driver-history` | Date of Birth, Driver Licence | HIGH |
| 4 | `/api/crashes/detail` | Full Name, Phone, Email | MEDIUM |
| 5 | `/api/crashes/search-suggest` | Email addresses | MEDIUM |

*Replace rows above with actual findings from the JSON report.*

---

## Detailed Findings

### Finding 1 — SSN Exposed in Report Export (CRITICAL)

**Endpoint:** `[URL]/api/crashes/report-export`  
**Access state:** Pre-authentication  
**Severity:** CRITICAL

**Description:**  
The `/api/crashes/report-export` endpoint returns a plaintext crash report
that includes the involved party's Social Security Number (SSN) without
requiring the caller to be authenticated or authorised.

**Evidence:**  
```
CRASH REPORT — CHI-2023-001
Driver: [REDACTED]
SSN: ***-**-****
```

**Impact:**  
Exposure of SSNs enables identity theft and fraudulent credit or insurance
applications.  This is a violation of federal law under the Gramm-Leach-Bliley
Act and, where applicable, state data-protection statutes.

**Remediation:**

1. **Immediately disable** unauthenticated access to the export endpoint.
2. Require session-based authentication (OAuth 2.0 / OIDC) before serving
   any report.
3. Remove SSNs from exported report files entirely; replace with a masked
   token or a last-4-digit representation only where legally required.
4. Implement field-level encryption for all PII stored in the database
   backing this endpoint.
5. Add automated regression tests that assert the endpoint returns HTTP 401
   when called without a valid token.

**References:**
- OWASP API Security Top 10 — API3:2023 Broken Object Property Level
  Authorization
- NIST SP 800-122 — Guide to Protecting the Confidentiality of Personally
  Identifiable Information

---

### Finding 2 — Insurance Data Exposed Pre-Authentication (HIGH)

**Endpoint:** `[URL]/api/crashes/insurance-lookup`  
**Access state:** Pre-authentication  
**Severity:** HIGH

**Description:**  
Insurance policy numbers and carrier information are returned to unauthenticated
callers.  This information is sufficient to make fraudulent claims.

**Remediation:**

1. Require authentication and role-based authorisation before returning any
   insurance record.
2. Ensure the API gateway enforces a deny-by-default policy: routes must be
   explicitly allow-listed for unauthenticated access.
3. Audit all insurance-data endpoints for similar misconfigurations.

---

### Finding 3 — Driver History Exposes DOB and Licence Number (HIGH)

**Endpoint:** `[URL]/api/crashes/driver-history`  
**Access state:** Pre-authentication  
**Severity:** HIGH

**Description:**  
Date of birth and driver-licence numbers are returned without authentication.
Combined with a name (available from `/api/crashes/detail`), this is sufficient
to impersonate the individual in state DMV queries.

**Remediation:**

1. Restrict the driver-history endpoint to authenticated users with a
   "law-enforcement" or "adjuster" role.
2. Log all accesses to this endpoint and alert on anomalous query volumes.
3. Mask the licence number in API responses (e.g., return only the last four
   digits).

---

### Finding 4 — PII in Crash Detail Endpoint (MEDIUM)

**Endpoint:** `[URL]/api/crashes/detail`  
**Access state:** Pre-authentication  
**Severity:** MEDIUM

**Description:**  
Full names, phone numbers, and email addresses of crash-involved parties are
returned to unauthenticated callers.

**Remediation:**

1. Require authentication before returning party-level contact information.
2. Consider returning only anonymised or aggregated data to unauthenticated
   consumers (e.g., crash location, date, injury count).

---

### Finding 5 — Email Leakage via Autocomplete (MEDIUM)

**Endpoint:** `[URL]/api/crashes/search-suggest`  
**Access state:** Pre-authentication  
**Severity:** MEDIUM

**Description:**  
The autocomplete / type-ahead endpoint returns email addresses of registered
users as suggestions, without authentication.  This allows enumeration of the
user base.

**Remediation:**

1. Restrict autocomplete suggestions to authenticated sessions only.
2. Ensure suggestions do not include PII fields such as email addresses;
   use display names or anonymised IDs instead.
3. Implement rate limiting on the endpoint to prevent bulk enumeration.

---

## General Recommendations

| Priority | Recommendation |
|----------|----------------|
| Immediate | Enforce authentication on all non-public endpoints (deny-by-default). |
| Immediate | Remove SSNs from any API response; store only masked representations. |
| Short-term | Implement role-based access control (RBAC) for sensitive data fields. |
| Short-term | Deploy an API gateway with centralised auth and audit logging. |
| Medium-term | Conduct a full data-classification exercise to identify all PII fields. |
| Medium-term | Introduce automated DAST (Dynamic Application Security Testing) in CI/CD. |
| Long-term | Adopt a zero-trust architecture for all internal services. |

---

## Regulatory Context

Depending on the jurisdiction and data types involved, the identified exposures
may constitute violations of:

- **Driver's Privacy Protection Act (DPPA)** — prohibits disclosure of
  personal information from motor-vehicle records without authorisation.
- **Gramm-Leach-Bliley Act (GLBA)** — requires financial institutions to
  protect consumer financial data.
- **California Consumer Privacy Act (CCPA)** / **CPRA** — grants consumers
  rights over their personal information.
- **HIPAA** — if any health/injury information is present in crash records.

Legal counsel should be engaged immediately to assess notification obligations.

---

## Conclusion

The findings documented in this report represent significant data-protection
risks that require **immediate remediation**.  The assessment team recommends
prioritising the CRITICAL and HIGH findings before the next business day and
completing all MEDIUM findings within 30 days.

A re-assessment should be conducted after remediation is complete to verify
that all vulnerabilities have been resolved.

---

*This report was generated using the alawconnect-ChicagoCrashes-1
ExposureScanner assessment tool.*  
*Template version: 1.0*
