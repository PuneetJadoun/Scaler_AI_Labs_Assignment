"""Entry point for the PII Redaction Tool pipeline.

Orchestrates the existing Reader, Detector, Replacement, and Writer
modules end to end: read a .docx file, detect PII, replace it with
realistic fake data, and write the redacted result into output/. This
module contains no PII-handling logic of its own - every decision about
what to detect or how to replace it is made by the module responsible for
it; this file only calls them in order and reports progress.

Usage:
    python src/main.py [path/to/file.docx]

If no path is given, the first .docx file found in input/ is used.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# The source document can contain characters (e.g. the Rupee sign, U+20B9)
# and this file prints U+2713 (✓), both of which fall outside Windows'
# default console/redirect encoding (cp1252) and would otherwise crash
# mid-pipeline with a UnicodeEncodeError.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC_ROOT = Path(__file__).resolve().parent
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from detectors.detector_manager import analyze_document  # noqa: E402
from document.reader import DocumentReaderError, read_document  # noqa: E402
from document.writer import DocumentWriterError, write_document  # noqa: E402
from replacement.replacement_manager import replace_entities  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = SRC_ROOT.parent
INPUT_DIR = PROJECT_ROOT / "input"
SEPARATOR = "=" * 44
DIVIDER = "-" * 44


def find_input_document() -> Path:
    """Return the document to process: a CLI arg, or the first .docx in input/."""
    if len(sys.argv) > 1:
        return Path(sys.argv[1])

    candidates = sorted(INPUT_DIR.glob("*.docx"))
    if not candidates:
        raise FileNotFoundError(
            f"No .docx file found in '{INPUT_DIR}'. "
            f"Place a document there or pass a path as an argument."
        )
    return candidates[0]


def run_pipeline(input_path: Path) -> Path:
    """Run Reader -> Detector -> Replacement -> Writer over `input_path`.

    Args:
        input_path: Path to the source .docx file.

    Returns:
        The path to the redacted .docx file written into output/.

    Raises:
        DocumentReaderError: The input file is missing, unreadable, or not
            a valid .docx (raised by the Reader).
        DocumentWriterError: The redacted document could not be written
            (raised by the Writer).
    """
    print("Reading document...")
    logger.info("Reading document: %s", input_path)
    document = read_document(input_path)
    print("✓ Completed")
    print(DIVIDER)
    print()

    print("Detecting PII...")
    logger.info("Running detector manager.")
    entities = analyze_document(document)
    logger.info("Detected %d entit(y/ies).", len(entities))
    print("✓ Completed")
    print(DIVIDER)
    print()

    print("Replacing PII...")
    logger.info("Running replacement manager over %d entit(y/ies).", len(entities))
    redacted_document = replace_entities(document, entities)
    print("✓ Completed")
    print(DIVIDER)
    print()

    print("Writing redacted document...")
    logger.info("Running writer module.")
    output_path = write_document(redacted_document)
    print("✓ Completed")
    print(DIVIDER)
    print()

    return output_path


def main() -> None:
    print(SEPARATOR)
    print()
    print("PII REDACTION TOOL")
    print()
    print(SEPARATOR)
    print()

    try:
        input_path = find_input_document()
    except FileNotFoundError as exc:
        logger.error("No input file available: %s", exc)
        print(f"Error: {exc}")
        sys.exit(1)

    print("Input File")
    print()
    print(input_path)
    print()
    print(DIVIDER)
    print()

    try:
        output_path = run_pipeline(input_path)
    except (DocumentReaderError, DocumentWriterError) as exc:
        logger.error("Pipeline failed: %s", exc)
        print(f"Error: {exc}")
        print()
        print(SEPARATOR)
        print("Pipeline Failed")
        print(SEPARATOR)
        sys.exit(1)
    except Exception:
        # The Detector and Replacement modules already contain their own
        # per-detector/per-replacer error handling and don't define typed
        # exceptions of their own; this is the fallback for a genuinely
        # unexpected failure anywhere in the pipeline.
        logger.exception("Unexpected pipeline failure.")
        print("Error: an unexpected failure occurred. See the log above for details.")
        print()
        print(SEPARATOR)
        print("Pipeline Failed")
        print(SEPARATOR)
        sys.exit(1)

    print("Output File")
    print()
    print(output_path)
    print()
    print(DIVIDER)
    print()
    print("Pipeline Completed Successfully")
    print()
    print(SEPARATOR)


if __name__ == "__main__":
    main()
