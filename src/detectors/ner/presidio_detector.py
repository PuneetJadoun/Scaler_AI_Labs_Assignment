"""Detects PERSON, ORGANIZATION, and LOCATION entities using Microsoft Presidio.

Presidio's AnalyzerEngine performs a single NLP pass over a piece of text
and can surface many entity types from that one pass, so — unlike the
regex detectors, which each own exactly one pattern — this file is not
split per entity type; splitting it would mean running the same expensive
NLP pipeline multiple times for no benefit.
"""

import logging
from functools import lru_cache

from models.entity import Entity

logger = logging.getLogger(__name__)

DETECTOR_SOURCE = "presidio"
SUPPORTED_ENTITIES = ["PERSON", "ORGANIZATION", "LOCATION"]
_LANGUAGE = "en"


class PresidioUnavailableError(RuntimeError):
    """Raised when Presidio or its underlying NLP engine cannot be loaded."""


# Presidio's own default.yaml lists ORGANIZATION in `labels_to_ignore`
# ("Has many false positives"), which silently drops every company-name
# detection before it ever reaches AnalyzerEngine.analyze() results. Since
# company names are a required PII type for this assignment, this config
# mirrors Presidio's default but removes ORGANIZATION from that ignore
# list. Trade-off: this knowingly accepts a higher false-positive rate on
# ORGANIZATION (per Presidio's own documented caveat) in exchange for
# actually detecting company names at all.
_NLP_CONFIGURATION = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}],
    "ner_model_configuration": {
        "model_to_presidio_entity_mapping": {
            "PER": "PERSON",
            "PERSON": "PERSON",
            "NORP": "NRP",
            "FAC": "LOCATION",
            "LOC": "LOCATION",
            "GPE": "LOCATION",
            "LOCATION": "LOCATION",
            "ORG": "ORGANIZATION",
            "ORGANIZATION": "ORGANIZATION",
            "DATE": "DATE_TIME",
            "TIME": "DATE_TIME",
        },
        "low_confidence_score_multiplier": 0.4,
        "low_score_entity_names": [],
        "labels_to_ignore": [
            "CARDINAL",
            "EVENT",
            "LANGUAGE",
            "LAW",
            "MONEY",
            "ORDINAL",
            "PERCENT",
            "PRODUCT",
            "QUANTITY",
            "WORK_OF_ART",
        ],
    },
}


@lru_cache(maxsize=1)
def _get_analyzer():
    """Lazily build and cache the AnalyzerEngine (expensive: loads an NLP model)."""
    try:
        from presidio_analyzer import AnalyzerEngine
        from presidio_analyzer.nlp_engine import NlpEngineProvider
    except ImportError as exc:
        raise PresidioUnavailableError(
            "presidio-analyzer is not installed. Install it with "
            "'pip install presidio-analyzer' and download a spaCy model, "
            "e.g. 'python -m spacy download en_core_web_lg'."
        ) from exc

    try:
        nlp_engine = NlpEngineProvider(nlp_configuration=_NLP_CONFIGURATION).create_engine()
        return AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=[_LANGUAGE])
    except Exception as exc:  # presidio/spaCy raise varied errors for a missing model
        raise PresidioUnavailableError(
            "Failed to initialize the Presidio analyzer. Ensure a spaCy "
            "NLP model is installed, e.g. 'python -m spacy download en_core_web_lg'."
        ) from exc


def detect_entities(text: str) -> list[Entity]:
    """Detect PERSON, ORGANIZATION, and LOCATION entities in `text`.

    Degrades gracefully instead of raising: returns an empty list for
    empty/whitespace-only text, and also (with a warning logged) if
    Presidio or its NLP model is unavailable, so a missing installation
    disables NER detection without breaking the rest of the pipeline.
    """
    if not text or not text.strip():
        return []

    try:
        analyzer = _get_analyzer()
    except PresidioUnavailableError:
        logger.warning("Presidio is unavailable; skipping NER detection.", exc_info=True)
        return []

    results = analyzer.analyze(text=text, entities=SUPPORTED_ENTITIES, language=_LANGUAGE)

    return [
        Entity(
            detected_text=text[result.start : result.end],
            entity_type=result.entity_type,
            confidence_score=result.score,
            detector_source=DETECTOR_SOURCE,
            start_offset=result.start,
            end_offset=result.end,
        )
        for result in results
    ]
