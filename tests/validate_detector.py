"""Manual validation script for the Detector Module.

This is NOT the final application and NOT a pytest/unittest suite. It is a
temporary, human-readable script used to validate that the Detector
Module correctly consumes a real Document and produces located, scored
Entity objects, before the Replacement Module is built on top of it.

Usage:
    python tests/validate_detector.py [path/to/file.docx]

If no path is given, the first .docx file found in input/ is used.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# The source document can contain characters (e.g. the Rupee sign, U+20B9)
# that fall outside Windows' default console/redirect encoding (cp1252),
# which would otherwise crash mid-report with a UnicodeEncodeError.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from detectors.detector_manager import analyze_document  # noqa: E402
from document.reader import DocumentReaderError, read_document  # noqa: E402
from models.entity import PARAGRAPH_LOCATION, Entity  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

INPUT_DIR = PROJECT_ROOT / "input"
SEPARATOR = "=" * 60
DIVIDER = "-" * 40

# entity_type -> human-readable summary label
_SUMMARY_LABELS: dict[str, str] = {
    "PERSON": "Persons",
    "EMAIL": "Emails",
    "PHONE_NUMBER": "Phones",
    "ORGANIZATION": "Companies",
    "LOCATION": "Addresses",
    "SSN": "SSNs",
    "CREDIT_CARD": "Credit Cards",
    "DATE_OF_BIRTH": "DOBs",
    "IP_ADDRESS": "IP Addresses",
}


def find_input_document() -> Path:
    """Return the document to validate: a CLI arg, or the first .docx in input/."""
    if len(sys.argv) > 1:
        return Path(sys.argv[1])

    candidates = sorted(INPUT_DIR.glob("*.docx"))
    if not candidates:
        raise FileNotFoundError(
            f"No .docx file found in '{INPUT_DIR}'. "
            f"Place a document there or pass a path as an argument."
        )
    return candidates[0]


def format_location(entity: Entity) -> str:
    """Human-readable location string, e.g. 'Paragraph 15' or 'Table 3 Row 2 Cell 1'."""
    if entity.location_type == PARAGRAPH_LOCATION:
        return f"Paragraph {entity.paragraph_index}"
    return f"Table {entity.table_index} Row {entity.row_index} Cell {entity.cell_index}"


def format_source(entity: Entity) -> str:
    """Human-readable detector source, e.g. 'Regex (regex.email)' or 'Presidio'."""
    if entity.detector_source.startswith("regex."):
        return f"Regex ({entity.detector_source})"
    return "Presidio"


def group_by_entity_type(entities: list[Entity]) -> dict[str, list[Entity]]:
    """Group entities by their entity_type, preserving first-seen type order."""
    groups: dict[str, list[Entity]] = {}
    for entity in entities:
        groups.setdefault(entity.entity_type, []).append(entity)
    return groups


def print_entities(groups: dict[str, list[Entity]]) -> None:
    print("Detected Entities")
    print()
    for entity_type, entities in groups.items():
        print(entity_type)
        print()
        for entity in entities:
            print(entity.detected_text)
            print()
            print("Location:")
            print(format_location(entity))
            print()
            print("Confidence:")
            print(f"{entity.confidence_score:.2f}")
            print()
            print("Source:")
            print(format_source(entity))
            print()
            print(DIVIDER)
        print()


def print_summary(groups: dict[str, list[Entity]], total: int) -> None:
    print(SEPARATOR)
    print()
    print("SUMMARY")
    print()
    for entity_type, label in _SUMMARY_LABELS.items():
        print(f"{label}: {len(groups.get(entity_type, []))}")

    other_types = set(groups) - set(_SUMMARY_LABELS)
    for entity_type in sorted(other_types):
        print(f"{entity_type}: {len(groups[entity_type])}")

    print()
    print(f"Total Entities: {total}")
    print()


def main() -> None:
    print(SEPARATOR)
    print("DETECTOR VALIDATION")
    print(SEPARATOR)
    print()

    document_path = find_input_document()
    print("Input File")
    print()
    print(document_path)
    print()
    print(DIVIDER)
    print()

    logger.info("Reading document: %s", document_path)
    document = read_document(document_path)
    print("Document Loaded Successfully")
    print()
    print(DIVIDER)
    print()

    logger.info(
        "Running detector manager over %d paragraphs and %d tables.",
        len(document.paragraphs),
        len(document.tables),
    )
    entities = analyze_document(document)
    groups = group_by_entity_type(entities)

    print_entities(groups)
    print_summary(groups, total=len(entities))

    print(SEPARATOR)
    print()
    print("Detector Validation Passed")
    print()
    print(SEPARATOR)


if __name__ == "__main__":
    try:
        main()
    except (DocumentReaderError, FileNotFoundError) as exc:
        logger.error("Detector validation failed: %s", exc)
        print()
        print(SEPARATOR)
        print(f"Detector Validation FAILED: {exc}")
        print(SEPARATOR)
        sys.exit(1)
