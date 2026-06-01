import pytest

from src.llm_client import parse_llm_json_response, strip_json_fences
from src.models import PersonalInfo


# --- strip_json_fences tests ---


def test_strip_json_fences_removes_json_block():
    """Strips ```json ... ``` fences and returns inner content."""
    raw = '```json\n{"key": "val"}\n```'
    assert strip_json_fences(raw) == '{"key": "val"}'


def test_strip_json_fences_removes_plain_block():
    """Strips ``` ... ``` fences (no language tag) and returns inner content."""
    raw = '```\n{"key": "val"}\n```'
    assert strip_json_fences(raw) == '{"key": "val"}'


def test_strip_json_fences_no_fences():
    """Returns the input unchanged when no fences are present."""
    raw = '{"key": "val"}'
    assert strip_json_fences(raw) == '{"key": "val"}'


def test_strip_json_fences_whitespace():
    """Trims leading/trailing whitespace when no fences are present."""
    raw = '  \n{"key": "val"}\n  '
    assert strip_json_fences(raw) == '{"key": "val"}'


# --- parse_llm_json_response tests ---


def test_parse_valid_json_matches_model():
    """Parses valid JSON and returns a PersonalInfo instance."""
    raw = '{"name": "Alice", "address": "123 Main St", "email": "alice@example.com", "phone": "555-1234"}'
    result = parse_llm_json_response(raw, PersonalInfo)
    assert isinstance(result, PersonalInfo)
    assert result.name == "Alice"
    assert result.address == "123 Main St"
    assert result.email == "alice@example.com"
    assert result.phone == "555-1234"
    assert result.linkedin is None


def test_parse_json_with_fences():
    """Parses JSON wrapped in markdown fences and returns a PersonalInfo instance."""
    raw = '```json\n{"name": "Bob", "address": "456 Oak Ave", "email": "bob@example.com", "phone": "555-5678", "linkedin": "https://linkedin.com/in/bob"}\n```'
    result = parse_llm_json_response(raw, PersonalInfo)
    assert isinstance(result, PersonalInfo)
    assert result.name == "Bob"
    assert result.linkedin == "https://linkedin.com/in/bob"


def test_parse_invalid_json_raises():
    """Raises ValueError with 'not valid JSON' when input is not JSON."""
    raw = "This is not JSON"
    with pytest.raises(ValueError, match="not valid JSON"):
        parse_llm_json_response(raw, PersonalInfo)


def test_parse_schema_mismatch_raises():
    """Raises ValueError with model name and 'schema' when fields don't match."""
    raw = '{"wrong_key": 1}'
    with pytest.raises(ValueError, match="PersonalInfo.*schema"):
        parse_llm_json_response(raw, PersonalInfo)
