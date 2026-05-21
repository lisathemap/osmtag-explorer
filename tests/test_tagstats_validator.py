"""Tests for tagstats.validator module."""
import pytest
from tagstats.validator import (
    ValidationResult,
    validate_key,
    validate_value,
    validate_tag,
)


class TestValidationResult:
    def test_bool_true_when_valid(self):
        assert bool(ValidationResult(True)) is True

    def test_bool_false_when_invalid(self):
        assert bool(ValidationResult(False, "some error")) is False

    def test_error_is_none_by_default_on_valid(self):
        assert ValidationResult(True).error is None


class TestValidateKey:
    def test_valid_simple_key(self):
        assert validate_key("highway")

    def test_valid_key_with_colon(self):
        assert validate_key("addr:street")

    def test_valid_key_with_underscore(self):
        assert validate_key("opening_hours")

    def test_valid_key_with_hyphen(self):
        assert validate_key("ref-isced")

    def test_empty_key_is_invalid(self):
        result = validate_key("")
        assert not result
        assert "empty" in result.error.lower()

    def test_key_starting_with_digit_is_invalid(self):
        result = validate_key("1way")
        assert not result

    def test_key_with_uppercase_is_invalid(self):
        result = validate_key("Highway")
        assert not result

    def test_key_with_space_is_invalid(self):
        result = validate_key("my key")
        assert not result

    def test_non_string_key_is_invalid(self):
        result = validate_key(123)  # type: ignore[arg-type]
        assert not result
        assert "string" in result.error.lower()

    def test_key_too_long_is_invalid(self):
        result = validate_key("a" * 256)
        assert not result


class TestValidateValue:
    def test_valid_value(self):
        assert validate_value("residential")

    def test_valid_value_with_spaces(self):
        assert validate_value("yes; no")

    def test_empty_value_is_invalid(self):
        result = validate_value("")
        assert not result
        assert "empty" in result.error.lower()

    def test_value_too_long_is_invalid(self):
        result = validate_value("x" * 256)
        assert not result

    def test_non_string_value_is_invalid(self):
        result = validate_value(None)  # type: ignore[arg-type]
        assert not result


class TestValidateTag:
    def test_valid_key_only(self):
        assert validate_tag("amenity")

    def test_valid_key_and_value(self):
        assert validate_tag("amenity", "cafe")

    def test_invalid_key_propagates(self):
        result = validate_tag("Bad Key", "value")
        assert not result

    def test_invalid_value_propagates(self):
        result = validate_tag("name", "")
        assert not result
        assert "empty" in result.error.lower()

    def test_none_value_skips_value_validation(self):
        assert validate_tag("highway", None)
