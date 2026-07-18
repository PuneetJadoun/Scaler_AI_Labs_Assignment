# Evaluation Report

## Objective

Evaluate the effectiveness of the PII redaction pipeline on a DOCX document while preserving document structure and readability.

---

## Test Document

- **Input:** `Red_Herring_Prospectus.docx`
- **Output:** `Red_Herring_Prospectus_redacted.docx`

---

## Supported PII Types

| PII Type | Detection Method |
|----------|------------------|
| Person Names | Microsoft Presidio (NER) |
| Company Names | Microsoft Presidio (NER) |
| Addresses | Microsoft Presidio (NER) |
| Email Addresses | Regex |
| Phone Numbers | Regex |
| SSN | Regex |
| Credit Card Numbers | Regex |
| Date of Birth | Regex |
| IP Addresses | Regex |

---

## Evaluation Approach

The evaluation was performed through manual comparison of the original and redacted documents.

The following aspects were verified:

- PII entities were replaced with realistic fake values.
- Repeated entities were replaced consistently.
- The generated DOCX opened successfully.
- Paragraphs and tables were preserved.
- Non-sensitive content remained readable after redaction.

---

## Results

| Metric | Result |
|--------|--------|
| Accuracy | Manual inspection indicates the generated output matches the expected redaction behavior for the evaluated document. |
| Precision | High – Most detected entities correspond to actual PII. Minor over-redaction may occur for some NER-detected entities. |
| Recall | High – The major visible PII entities (names, emails, phone numbers, company names and addresses) were successfully redacted during manual inspection. |
| Document Integrity | Passed |
| Replacement Consistency | Passed |

---

## Observations

- Email addresses and phone numbers were reliably detected using regular expressions.
- Person names, company names and addresses were detected using Microsoft Presidio.
- The output document remained readable and preserved the original structure.
- Tables and paragraphs were retained after redaction.
- The test document did not contain representative examples of every supported PII type (such as SSNs or credit card numbers).

---

## Conclusion

The implemented solution successfully performs end-to-end PII redaction for DOCX documents. Manual evaluation indicates good precision and high recall for the provided test document while preserving document structure and readability. The implementation satisfies the expected assignment deliverables.