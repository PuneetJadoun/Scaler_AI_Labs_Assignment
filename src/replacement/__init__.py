"""Replacement module: replaces detected PII in a Document with fake values.

Consumers should use `replace_entities` exclusively; the individual
replacers and the Faker provider underneath are internal to this package.
This module only ever produces a new, in-memory Document — it never
writes a .docx file.
"""

from replacement.replacement_manager import replace_entities

__all__ = ["replace_entities"]
