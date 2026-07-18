"""Replaces detected dates of birth with fake ones."""

from models.entity import Entity
from replacement.faker_provider import fake_date_of_birth


def replace_dob(entity: Entity) -> str:
    """Generate a fake replacement for a detected DATE_OF_BIRTH entity."""
    return fake_date_of_birth()
