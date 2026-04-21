# alawconnect-ChicagoCrashes-1


## Remediation Readiness

To address the detected high-severity exposures, it is recommended to:

- **Implement Data Masking:** Ensure that sensitive fields such as phone numbers, email addresses, mailing addresses, and insurance IDs are masked or redacted before data is published or shared externally.
- **Enforce IDOR (Insecure Direct Object Reference) Protection:** Apply strict access controls and validation to prevent unauthorized access to records via predictable identifiers or URLs. Ensure that users can only access data they are explicitly authorized to view.

These steps will help mitigate the risk of PII exposure and improve the overall security posture of the data portal.