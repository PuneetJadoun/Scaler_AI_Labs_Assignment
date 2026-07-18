"""Detector module: finds PII in a Document without ever modifying it.

Consumers should use `analyze_document` exclusively; the regex and NER
detector implementations underneath are internal to this package.
"""

from detectors.detector_manager import analyze_document

__all__ = ["analyze_document"]
