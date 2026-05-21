"""Validation utilities for OSM tag keys and values."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# OSM tag keys: lowercase letters, digits, colons, underscores, hyphens
_KEY_RE = re.compile(r'^[a-z][a-z0-9:_-]{0,254}$')
# OSM tag values: any non-empty string up to 255 chars
_VALUE_RE = re.compile(r'^.{1,255}$')


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    error: Optional[str] = None

    def __bool__(self) -> bool:
        return self.valid


def validate_key(key: str) -> ValidationResult:
    """Validate an OSM tag key."""
    if not isinstance(key, str):
        return ValidationResult(False, "Key must be a string")
    if not key:
        return ValidationResult(False, "Key must not be empty")
    if not _KEY_RE.match(key):
        return ValidationResult(
            False,
            f"Key '{key}' is invalid: must start with a lowercase letter and "
            "contain only lowercase letters, digits, colons, underscores, or hyphens",
        )
    return ValidationResult(True)


def validate_value(value: str) -> ValidationResult:
    """Validate an OSM tag value."""
    if not isinstance(value, str):
        return ValidationResult(False, "Value must be a string")
    if not value:
        return ValidationResult(False, "Value must not be empty")
    if not _VALUE_RE.match(value):
        return ValidationResult(False, f"Value exceeds 255 characters")
    return ValidationResult(True)


def validate_tag(key: str, value: Optional[str] = None) -> ValidationResult:
    """Validate an OSM tag key and optional value together."""
    key_result = validate_key(key)
    if not key_result:
        return key_result
    if value is not None:
        value_result = validate_value(value)
        if not value_result:
            return value_result
    return ValidationResult(True)
