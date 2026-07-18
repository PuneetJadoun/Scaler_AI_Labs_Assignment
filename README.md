# DOCX PII Redaction Tool

## Project Overview

This project is a Python-based tool that detects and redacts Personally Identifiable Information (PII) from Microsoft Word (`.docx`) documents. It identifies sensitive information, replaces it with realistic synthetic values, and generates a new redacted document while preserving the original document structure.

---

## Features

- Reads Microsoft Word (`.docx`) documents.
- Detects multiple types of Personally Identifiable Information (PII).
- Replaces detected PII with realistic fake values.
- Maintains consistent replacements for repeated entities.
- Preserves document structure, including paragraphs and tables.
- Generates a redacted DOCX document.

---

## Supported PII Types

| PII Type | Detection Method |
|----------|------------------|
| Person Names | Microsoft Presidio (NER) |
| Company Names | Microsoft Presidio (NER) |
| Physical Addresses | Microsoft Presidio (NER) |
| Email Addresses | Regular Expressions |
| Phone Numbers | Regular Expressions |
| Social Security Numbers (SSN) | Regular Expressions |
| Credit Card Numbers | Regular Expressions |
| Dates of Birth | Regular Expressions |
| IP Addresses | Regular Expressions |

---

## Project Structure

```text
PII-Redaction/
│
├── input/                  # Input DOCX documents
├── output/                 # Generated redacted documents
├── reports/                # Evaluation report
├── src/
│   ├── detectors/          # PII detection modules
│   ├── document/           # DOCX reader and writer
│   ├── models/             # Shared data models
│   ├── replacement/        # PII replacement logic
│   ├── utils/              # Utility functions
│   └── main.py             # Application entry point
│
├── tests/                  # Validation scripts
├── requirements.txt
└── README.md
```

---

## Workflow

```text
                 +------------------+
                 |  Input DOCX File |
                 +------------------+
                          |
                          v
                 +------------------+
                 |  Document Reader |
                 +------------------+
                          |
                          v
          +----------------------------------+
          |      PII Detection               |
          |  Presidio (NER) + Regex Rules    |
          +----------------------------------+
                          |
                          v
          +----------------------------------+
          |      PII Replacement             |
          |   Faker + Consistent Mapping     |
          +----------------------------------+
                          |
                          v
                 +------------------+
                 | Document Writer  |
                 +------------------+
                          |
                          v
               +------------------------+
               | Redacted DOCX Document |
               +------------------------+
```

---

## Approach

The redaction pipeline consists of four stages:

1. **Document Reader**
   - Reads the input DOCX document.
   - Extracts text from paragraphs and tables.

2. **PII Detection**
   - Uses Microsoft Presidio for detecting person names, company names, and addresses.
   - Uses Regular Expressions for detecting structured PII such as email addresses, phone numbers, SSNs, credit card numbers, dates of birth, and IP addresses.

3. **PII Replacement**
   - Replaces detected PII with realistic fake values generated using Faker.
   - Maintains consistent replacements for repeated occurrences of the same entity.

4. **Document Writer**
   - Reconstructs the document using the modified content.
   - Saves the redacted document to the `output/` directory.

---

## Technologies Used

- Python
- python-docx
- Microsoft Presidio
- Faker
- Regular Expressions

---

## How to Run

### Prerequisites

- Python 3.10 or later (the codebase uses `X | Y` union type hints evaluated at runtime, which requires 3.10+)
- pip

### Installation

Run all commands from the project root.

1. Create and activate a virtual environment:

   **Windows (PowerShell)**
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   **macOS / Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install the Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### One-Time Setup

The NER detector (Microsoft Presidio) requires a spaCy language model that is **not** installed by `pip install -r requirements.txt` — it must be downloaded separately:

```bash
python -m spacy download en_core_web_lg
```

Without this step, person/company/address detection will silently be skipped (the pipeline still runs, but with materially incomplete redaction), so don't skip it.

### Running the Application

1. Place the `.docx` file(s) you want redacted into `input/` (this folder is empty by default — input documents are gitignored and not shipped with the repo).
2. Run the pipeline:
   ```bash
   python src/main.py
   ```
   This processes the first `.docx` file found in `input/`. To target a specific file instead:
   ```bash
   python src/main.py "input/YourFile.docx"
   ```

### Input / Output Locations

| | Location |
|---|---|
| Input | `input/` — the file to redact (first `.docx` found, or the path passed as an argument) |
| Output | `output/` — created automatically if missing; the redacted file is named `<original-name>_redacted.docx` |

---

## Evaluation Summary

The implementation was evaluated by manually comparing the original and redacted documents.

The evaluation verified:

- Correct detection and replacement of supported PII.
- Consistent replacement of repeated entities.
- Preservation of document structure, including paragraphs and tables.
- Successful generation of a valid redacted DOCX document.

A detailed evaluation is available in **`reports/evaluation_report.md`**.