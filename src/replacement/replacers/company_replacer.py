"""Replaces detected company names with fake ones."""

from models.entity import Entity
from replacement.faker_provider import fake_company_name


def replace_company(entity: Entity) -> str:
    """Generate a fake replacement for a detected ORGANIZATION entity."""
    return fake_company_name()
