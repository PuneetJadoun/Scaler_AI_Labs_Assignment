"""Replaces detected phone numbers with fake ones."""

from models.entity import Entity
from replacement.faker_provider import fake_phone_number


def replace_phone(entity: Entity) -> str:
    """Generate a fake replacement for a detected PHONE_NUMBER entity."""
    return fake_phone_number()
