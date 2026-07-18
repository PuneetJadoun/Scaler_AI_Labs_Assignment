"""Replaces detected Social Security Numbers with fake ones."""

from models.entity import Entity
from replacement.faker_provider import fake_ssn


def replace_ssn(entity: Entity) -> str:
    """Generate a fake replacement for a detected SSN entity."""
    return fake_ssn()
