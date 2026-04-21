"""
Main entry point for the Municipal Portal Privacy Assessment Prototype.
"""
import argparse
import json
from assessor.inspector import ExposureInspector
from assessor.reporter import ExposureReporter
from assessor.assessment_reporter import AssessmentReporter

# Example config object for AssessmentReporter
class SimpleConfig:
    target_base_url = "https://data.cityofchicago.org/resource/85ca-t3if.json"
    authorized = False

def main():
    parser = argparse.ArgumentParser(description="Municipal Portal Privacy Assessment Prototype")
    parser.add_argument("--target", type=str, default=SimpleConfig.target_base_url, help="Target API URL to audit")
    parser.add_argument("--output", type=str, default="findings.json", help="Output file for findings")
    parser.add_argument("--report", type=str, default="assessment_report.json", help="Output file for summary report")
    parser.add_argument("--mode", type=str, choices=["mock", "live"], default="live", help="Audit mode: mock or live")
    args = parser.parse_args()

    # Fetch data
    if args.mode == "mock":
        # Example mock data
        records = [
            {"phone": "312-555-4821", "email": "test@example.com", "address": "123 Main St.", "insurance": "ABC1234567"},
            {"phone": "773-555-1234", "email": "foo@bar.com", "address": "456 Oak Ave.", "insurance": "XYZ9876543"}
        ]
    else:
        import requests
        resp = requests.get(args.target, timeout=30)
        resp.raise_for_status()
        records = resp.json()
        if isinstance(records, dict) and "data" in records:
            records = records["data"]

    # Inspect exposures
    inspector = ExposureInspector()
    findings = inspector.inspect_batch(records, use_mock=(args.mode=="mock"), endpoint=args.target)

    # Save findings
    reporter = ExposureReporter(output_file=args.output)
    reporter.save_findings({"issues": findings})
    reporter.print_summary({"issues": findings})

    # Generate and save summary report
    assessment_reporter = AssessmentReporter()
    config = SimpleConfig()
    config.target_base_url = args.target
    summary = assessment_reporter.generate_summary_report(config, findings)
    assessment_reporter.save_report(summary, filename=args.report)

if __name__ == "__main__":
    main()
