"""Manual validation script for the Writer Module.

This is NOT the final application and NOT a pytest/unittest suite. It is a
temporary, human-readable script that runs the complete Reader -> Detector
-> Replacement -> Writer pipeline over a real Document and confirms the
Writer produced a valid, structurally-intact .docx file in output/, before
everything is wired together in main.py.

Formatting (fonts, styles, bold/italic, etc.) is explicitly out of scope:
this only checks that the document was generated, its structure survived,
and it can be opened and read back successfully.

Usage:
    python tests/validate_writer.py [path/to/file.docx]

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
from document.models.document import Document  # noqa: E402
from document.reader import DocumentReaderError, read_document  # noqa: E402
from document.writer import DocumentWriterError, write_document  # noqa: E402
from replacement.replacement_manager import replace_entities  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

INPUT_DIR = PROJECT_ROOT / "input"
SEPARATOR = "=" * 60
DIVIDER = "-" * 60


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


def cell_count(document: Document) -> int:
    """Total number of table cells across every table in `document`."""
    return sum(len(row.cells) for table in document.tables for row in table.rows)


def row_count(document: Document) -> int:
    """Total number of rows across every table in `document`."""
    return sum(len(table.rows) for table in document.tables)


def print_status(label: str, passed: bool) -> None:
    print(label)
    print()
    print("PASS" if passed else "FAIL")
    print()
    print(DIVIDER)
    print()


def main() -> None:
    print(SEPARATOR)
    print()
    print("WRITER VALIDATION")
    print()
    print(SEPARATOR)
    print()

    input_path = find_input_document()
    print("Input File")
    print()
    print(input_path)
    print()
    print(DIVIDER)
    print()

    logger.info("Reading document: %s", input_path)
    original_document = read_document(input_path)
    logger.info(
        "Reader: %d paragraph(s), %d table(s).",
        len(original_document.paragraphs),
        len(original_document.tables),
    )

    logger.info("Running detector manager.")
    entities = analyze_document(original_document)
    logger.info("Detector: %d entit(y/ies) detected.", len(entities))

    logger.info("Running replacement manager.")
    replaced_document = replace_entities(original_document, entities)
    logger.info("Replacement: document rewritten in memory.")

    logger.info("Running writer module.")
    output_path = write_document(replaced_document)
    logger.info("Writer: saved to '%s'.", output_path)

    print("Output File")
    print()
    print(output_path)
    print()
    print(DIVIDER)
    print()

    print("Pipeline")
    print()
    print("✓ Reader")
    print("✓ Detector")
    print("✓ Replacement")
    print("✓ Writer")
    print()
    print(DIVIDER)
    print()

    output_exists = output_path.exists() and output_path.is_file()
    print_status("Output File Created", output_exists)

    output_size_kb = output_path.stat().st_size / 1024 if output_exists else 0.0
    print("Output File Size")
    print()
    print(f"{output_size_kb:.1f} KB")
    print()
    print(DIVIDER)
    print()

    print_status("Output File Exists", output_exists)
    print_status("Document Successfully Written", output_exists and output_size_kb > 0)

    print(SEPARATOR)
    print()
    print("VALIDATION SUMMARY")
    print()

    # Read the written file back through the same Reader used at the top
    # of the pipeline, so "does the output hold what we wrote" is checked
    # with the one module in the codebase whose job is reading .docx files.
    reopened_document: Document | None = None
    reopen_ok = True
    try:
        reopened_document = read_document(output_path)
    except DocumentReaderError as exc:
        reopen_ok = False
        logger.error("Could not reopen the written document: %s", exc)

    if reopened_document is not None:
        expected_paragraphs = len(replaced_document.paragraphs)
        written_paragraphs = len(reopened_document.paragraphs)
        print("Paragraph Count")
        print()
        print("Original")
        print()
        print(expected_paragraphs)
        print()
        print("Written")
        print()
        print(written_paragraphs)
        print()
        print_status("Status", written_paragraphs == expected_paragraphs)

        expected_tables = len(replaced_document.tables)
        written_tables = len(reopened_document.tables)
        print("Table Count")
        print()
        print("Original")
        print()
        print(expected_tables)
        print()
        print("Written")
        print()
        print(written_tables)
        print()
        print_status("Status", written_tables == expected_tables)

        expected_rows = row_count(replaced_document)
        written_rows = row_count(reopened_document)
        print_status("Row Count", written_rows == expected_rows)

        expected_cells = cell_count(replaced_document)
        written_cells = cell_count(reopened_document)
        print_status("Cell Count", written_cells == expected_cells)
    else:
        expected_paragraphs = written_paragraphs = 0
        expected_tables = written_tables = 0
        expected_rows = written_rows = 0
        expected_cells = written_cells = 0

    print_status("Output File Opens Successfully", reopen_ok)

    all_passed = (
        output_exists
        and output_size_kb > 0
        and reopen_ok
        and written_paragraphs == expected_paragraphs
        and written_tables == expected_tables
        and written_rows == expected_rows
        and written_cells == expected_cells
    )

    print(SEPARATOR)
    print()
    if all_passed:
        print("Writer Validation Passed")
    else:
        print("Writer Validation FAILED")
    print()
    print(SEPARATOR)

    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except (DocumentReaderError, DocumentWriterError, FileNotFoundError) as exc:
        logger.error("Writer validation failed: %s", exc)
        print()
        print(SEPARATOR)
        print(f"Writer Validation FAILED: {exc}")
        print(SEPARATOR)
        sys.exit(1)
