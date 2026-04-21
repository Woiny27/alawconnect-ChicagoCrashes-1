#!/usr/bin/env python3
"""
Data Audit Script for Chicago Crashes Dataset
Fetches and validates data from the Chicago data portal
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests
from collections import defaultdict


# Mock data for testing
MOCK_DATA = [
    {
        "crash_id": "12345",
        "crash_date": "2024-01-15",
        "crash_location": "POINT (-87.6298 41.8781)",
        "injuries": "2",
        "fatalities": "0",
        "primary_cause": "Following too closely",
        "weather_condition": "Clear"
    },
    {
        "crash_id": "12346",
        "crash_date": "2024-01-16",
        "crash_location": "POINT (-87.6200 41.8850)",
        "injuries": "1",
        "fatalities": "1",
        "primary_cause": "Failure to yield",
        "weather_condition": "Rainy"
    },
    {
        "crash_id": "12347",
        "crash_date": "2024-01-17",
        "crash_location": "POINT (-87.6150 41.8900)",
        "injuries": None,
        "fatalities": "0",
        "primary_cause": "Speeding",
        "weather_condition": "Clear"
    }
]


class DataAuditor:
    """Performs data quality audits on crash data"""
    
    def __init__(self, target_url: Optional[str] = None, use_mock: bool = False):
        self.target_url = target_url
        self.use_mock = use_mock
        self.data = []
        self.findings = {
            "summary": {},
            "data_quality": {},
            "issues": [],
            "timestamp": datetime.now().isoformat()
        }
    
    def fetch_data(self) -> bool:
        """Fetch data from the target URL or use mock data"""
        try:
            if self.use_mock:
                print("📋 Using mock data for audit")
                self.data = MOCK_DATA
                return True
            
            if not self.target_url:
                print("❌ No target URL provided and mock mode is disabled")
                return False
            
            print(f"🌐 Fetching data from: {self.target_url}")
            response = requests.get(self.target_url, timeout=30)
            response.raise_for_status()
            
            # Handle both direct JSON array and paginated responses
            resp_data = response.json()
            if isinstance(resp_data, list):
                self.data = resp_data
            elif isinstance(resp_data, dict) and "data" in resp_data:
                self.data = resp_data["data"]
            else:
                self.data = [resp_data]
            
            print(f"✅ Successfully fetched {len(self.data)} records")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching data: {e}")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON: {e}")
            return False
    
    def analyze_schema(self) -> None:
        """Analyze the schema and data types"""
        if not self.data:
            return
        
        field_types = defaultdict(set)
        field_nulls = defaultdict(int)
        
        for record in self.data:
            for key, value in record.items():
                if value is None:
                    field_nulls[key] += 1
                else:
                    field_types[key].add(type(value).__name__)
        
        self.findings["data_quality"]["fields"] = {}
        for field_name in sorted(field_types.keys()):
            types_found = list(field_types[field_name])
            null_count = field_nulls[field_name]
            
            self.findings["data_quality"]["fields"][field_name] = {
                "data_types": types_found,
                "null_count": null_count,
                "null_percentage": round(100 * null_count / len(self.data), 2)
            }
            
            # Flag issues
            if null_count > len(self.data) * 0.2:  # More than 20% nulls
                self.findings["issues"].append({
                    "severity": "warning",
                    "field": field_name,
                    "issue": f"High null rate: {null_count}/{len(self.data)} ({round(100*null_count/len(self.data), 1)}%)"
                })
            
            if len(types_found) > 1:
                self.findings["issues"].append({
                    "severity": "info",
                    "field": field_name,
                    "issue": f"Mixed data types: {', '.join(types_found)}"
                })
    
    def validate_crashes(self) -> None:
        """Validate crash-specific data"""
        crash_ids = set()
        date_range = {"min": None, "max": None}
        injuries_total = 0
        fatalities_total = 0
        
        for idx, record in enumerate(self.data):
            # Check for duplicate IDs
            crash_id = record.get("crash_id")
            if crash_id:
                if crash_id in crash_ids:
                    self.findings["issues"].append({
                        "severity": "error",
                        "record_index": idx,
                        "issue": f"Duplicate crash_id: {crash_id}"
                    })
                crash_ids.add(crash_id)
            
            # Track date range
            crash_date = record.get("crash_date")
            if crash_date:
                if date_range["min"] is None or crash_date < date_range["min"]:
                    date_range["min"] = crash_date
                if date_range["max"] is None or crash_date > date_range["max"]:
                    date_range["max"] = crash_date
            
            # Sum injuries and fatalities
            injuries = record.get("injuries")
            if injuries is not None:
                try:
                    injuries_total += int(injuries)
                except (ValueError, TypeError):
                    self.findings["issues"].append({
                        "severity": "warning",
                        "record_index": idx,
                        "issue": f"Invalid injuries value: {injuries}"
                    })
            
            fatalities = record.get("fatalities")
            if fatalities is not None:
                try:
                    fatalities_total += int(fatalities)
                except (ValueError, TypeError):
                    self.findings["issues"].append({
                        "severity": "warning",
                        "record_index": idx,
                        "issue": f"Invalid fatalities value: {fatalities}"
                    })
        
        self.findings["data_quality"]["stats"] = {
            "unique_crash_ids": len(crash_ids),
            "date_range": date_range,
            "total_injuries": injuries_total,
            "total_fatalities": fatalities_total
        }
    
    def run_audit(self) -> bool:
        """Execute the full audit"""
        print("\n" + "="*60)
        print("🔍 CHICAGO CRASHES DATA AUDIT")
        print("="*60 + "\n")
        
        # Fetch data
        if not self.fetch_data():
            return False
        
        # Generate summary
        self.findings["summary"]["total_records"] = len(self.data)
        self.findings["summary"]["audit_mode"] = "mock" if self.use_mock else "live"
        
        print("\n📊 Analyzing schema...")
        self.analyze_schema()
        
        print("✔️  Validating crash data...")
        self.validate_crashes()
        
        # Report findings
        print(f"\n📈 Results:")
        print(f"   Total Records: {self.findings['summary']['total_records']}")
        if "stats" in self.findings["data_quality"]:
            stats = self.findings["data_quality"]["stats"]
            print(f"   Unique Crash IDs: {stats['unique_crash_ids']}")
            print(f"   Date Range: {stats['date_range']['min']} to {stats['date_range']['max']}")
            print(f"   Total Injuries: {stats['total_injuries']}")
            print(f"   Total Fatalities: {stats['total_fatalities']}")
        
        # Report issues
        issue_counts = defaultdict(int)
        for issue in self.findings["issues"]:
            issue_counts[issue["severity"]] += 1
        
        if self.findings["issues"]:
            print(f"\n⚠️  Issues Found:")
            for severity in ["error", "warning", "info"]:
                if issue_counts[severity] > 0:
                    print(f"   {severity.upper()}: {issue_counts[severity]}")
        else:
            print(f"\n✅ No issues found!")
        
        return True
    
    def get_findings(self) -> Dict[str, Any]:
        """Return audit findings"""
        return self.findings
    
    def save_findings(self, output_file: str) -> bool:
        """Save findings to JSON file"""
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(self.findings, f, indent=2)
            
            print(f"\n💾 Findings saved to: {output_file}")
            return True
        except Exception as e:
            print(f"❌ Error saving findings: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Audit script for Chicago Crashes data"
    )
    parser.add_argument(
        "--target",
        type=str,
        help="Target API URL to audit",
        default=None
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["mock", "live"],
        default="live",
        help="Audit mode: mock (use sample data) or live (fetch from URL)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="findings.json",
        help="Output file for audit findings (JSON)"
    )
    
    args = parser.parse_args()
    
    # Run audit
    auditor = DataAuditor(
        target_url=args.target,
        use_mock=(args.mode == "mock")
    )
    
    if not auditor.run_audit():
        return 1
    
    # Save findings
    if not auditor.save_findings(args.output):
        return 1
    
    print("\n" + "="*60)
    print("✨ Audit Complete!")
    print("="*60 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
