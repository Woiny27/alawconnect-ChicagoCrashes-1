import requests
from bs4 import BeautifulSoup
import json
import re
from .config import SENSITIVE_FIELDS

class ExposureInspector:
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config.user_agent})

    def check_endpoint(self, endpoint: str):
        url = self.config.target_base_url.rstrip("/") + endpoint
        try:
            response = self.session.get(url, timeout=self.config.timeout, allow_redirects=True)
            response.raise_for_status()
            
            findings = self._analyze_response(response, endpoint)
            return findings
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "endpoint": endpoint, "access_state": "failed"}

    def _analyze_response(self, response, endpoint):
        findings = []
        content_type = response.headers.get("Content-Type", "")
        
        if "application/json" in content_type:
            try:
                data = response.json()
                findings.extend(self._scan_json(data, endpoint))
            except json.JSONDecodeError:
                pass
        else:
            # HTML/text
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text()
            findings.extend(self._scan_text(text, endpoint))
            
            # Check for exposed JSON in scripts or data attributes
            scripts = soup.find_all("script", type="application/json")
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    findings.extend(self._scan_json(data, endpoint))
                except:
                    pass
        
        return findings

    def _scan_text(self, text: str, endpoint: str):
        findings = []
        for field_type, patterns in SENSITIVE_FIELDS.items():
            for pattern in patterns:
                # Simple regex for potential exposure (demo only; improve with context)
                matches = re.findall(rf"(?i)(?:{pattern})\s*[:=]\s*([^\s,]+)", text)
                for match in matches[:2]:  # Limit samples
                    if match and len(match) > 3:  # Basic validation
                        findings.append({
                            "field_detected": field_type,
                            "endpoint": endpoint,
                            "access_state": "pre-authentication" if "login" not in endpoint else "post-auth",
                            "sample_value": "[REDACTED_FOR_SAFETY]",  # Never expose real PII
                            "severity": "high" if field_type in ["phone_number", "email"] else "medium",
                            "evidence_snippet": "Pattern matched in public response"
                        })
        return findings

    def _scan_json(self, data: dict, endpoint: str):
        findings = []
        # Recursive scan (simplified)
        def recurse(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    for field_type, patterns in SENSITIVE_FIELDS.items():
                        if any(p.lower() in k.lower() for p in patterns):
                            findings.append({
                                "field_detected": field_type,
                                "endpoint": endpoint,
                                "access_state": "pre-authentication",
                                "sample_value": "[REDACTED_FOR_SAFETY]",
                                "severity": "high",
                                "evidence_snippet": f"Key '{k}' in JSON at {path}"
                            })
                    recurse(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for item in obj[:5]:  # Limit depth
                    recurse(item, path)
        
        recurse(data)
        return findings