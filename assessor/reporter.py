import json
from datetime import datetime
from typing import List, Dict

class AssessmentReporter:
    def generate_findings(self, all_findings: List[Dict]) -> List[Dict]:
        # Deduplicate, etc. (basic)
        return all_findings

    def generate_summary_report(self, config, findings: List[Dict]) -> Dict:
        exposed_fields = set(f["field_detected"] for f in findings if "field_detected" in f)
        
        report = {
            "assessment_date": datetime.utcnow().isoformat(),
            "target": config.target_base_url,
            "authorized": config.authorized,
            "total_findings": len(findings),
            "exposed_sensitive_fields": list(exposed_fields),
            "summary": f"Found potential exposure of {len(exposed_fields)} sensitive field types.",
            "business_impact": "High risk of privacy violations (e.g., GDPR/CCPA equivalents, driver data breach). Could lead to regulatory fines, loss of public trust, and legal liability for the municipal entity.",
            "recommendations": [
                "Implement proper authentication (OAuth/JWT) and authorization checks on all report-related endpoints.",
                "Redact or pseudonymize PII in public/preview workflows.",
                "Use server-side rendering with access controls; avoid client-side exposure of raw data.",
                "Add rate limiting, logging, and monitoring for anomalous access.",
                "Conduct regular penetration testing and privacy impact assessments (PIA).",
                "Consider token-based access tied to verified involved-party status."
            ],
            "findings": self.generate_findings(findings)
        }
        return report

    def save_report(self, report: Dict, filename: str = "assessment_report.json"):
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to {filename}")