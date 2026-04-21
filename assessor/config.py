import os
from dataclasses import dataclass
from typing import List

SENSITIVE_FIELDS = {
    "name": ["name", "full_name", "driver_name"],
    "phone_number": ["phone", "telephone", "contact_phone"],
    "mailing_address": ["address", "mailing", "street"],
    "email": ["email", "e-mail"],
    "insurance_identifier": ["insurance", "policy", "vin"]  # Adjust as needed
}

@dataclass
class AssessmentConfig:
    target_base_url: str
    authorized: bool = False
    endpoints_to_check: List[str] = None  # e.g., ["/report/preview", "/search", "/api/public"]
    user_agent: str = "Authorized-Privacy-Assessor-Prototype/1.0"
    timeout: int = 10

    def __post_init__(self):
        if not self.authorized:
            raise ValueError("Explicit authorization required for any assessment.")
        if not self.endpoints_to_check:
            self.endpoints_to_check = ["/", "/report/preview", "/search", "/api/reports"]