"""Replaces detected person names with fake ones."""

from models.entity import Entity
from replacement.faker_provider import fake_person_name


def replace_person(entity: Entity) -> str:
    """Generate a fake replacement for a detected PERSON entity.

    `entity` is accepted (rather than a bare string) for interface
    consistency with every other replacer, some of which do use fields of
    the original entity (see email_replacer).
    """
    return fake_person_name()
