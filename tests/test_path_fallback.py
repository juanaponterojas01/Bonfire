"""Tests for path-fallback logic in src.orchestrator."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.orchestrator import _load_or_extract_profile, _load_summary, _resolve_template


# ---------------------------------------------------------------------------
# _resolve_template
# ---------------------------------------------------------------------------


def test_resolve_template_returns_primary_when_exists(tmp_path, monkeypatch):
    """When the primary template exists, its path is returned."""
    # Arrange
    monkeypatch.chdir(tmp_path)
    primary = tmp_path / "templates" / "en" / "cover_letter_template.docx"
    primary.parent.mkdir(parents=True, exist_ok=True)
    primary.write_text("dummy")

    # Act
    result = _resolve_template("en", "cover_letter_template.docx")

    # Assert
    assert result == str(Path("templates/en/cover_letter_template.docx"))


def test_resolve_template_falls_back_when_primary_missing(tmp_path, monkeypatch):
    """When the primary is missing but the fallback exists, the fallback path is returned."""
    # Arrange
    monkeypatch.chdir(tmp_path)
    fallback = (
        tmp_path / "examples" / "templates" / "en" / "cover_letter_template.docx"
    )
    fallback.parent.mkdir(parents=True, exist_ok=True)
    fallback.write_text("dummy")

    # Act
    result = _resolve_template("en", "cover_letter_template.docx")

    # Assert
    assert result == str(Path("examples/templates/en/cover_letter_template.docx"))


def test_resolve_template_raises_when_both_missing(tmp_path, monkeypatch):
    """When neither primary nor fallback exists, FileNotFoundError is raised."""
    # Arrange
    monkeypatch.chdir(tmp_path)

    # Act & Assert
    with pytest.raises(FileNotFoundError, match="not found for language 'en'"):
        _resolve_template("en", "cover_letter_template.docx")


# ---------------------------------------------------------------------------
# _load_summary
# ---------------------------------------------------------------------------


def test_load_summary_reads_from_primary_when_exists(tmp_path, monkeypatch):
    """When the primary summary exists, its content is read and returned."""
    # Arrange
    monkeypatch.chdir(tmp_path)
    primary = tmp_path / "data" / "background_md" / "background_english.md"
    primary.parent.mkdir(parents=True, exist_ok=True)
    primary.write_text("English background content", encoding="utf-8")

    # Act
    result = _load_summary("en")

    # Assert
    assert result == "English background content"


def test_load_summary_falls_back_when_primary_missing(tmp_path, monkeypatch):
    """When primary is missing but fallback exists, content is read from fallback."""
    # Arrange
    monkeypatch.chdir(tmp_path)
    fallback = (
        tmp_path / "examples" / "data" / "background_md" / "background_english.md"
    )
    fallback.parent.mkdir(parents=True, exist_ok=True)
    fallback.write_text("Fallback English content", encoding="utf-8")

    # Act
    result = _load_summary("en")

    # Assert
    assert result == "Fallback English content"


def test_load_summary_raises_when_both_missing(tmp_path, monkeypatch):
    """When neither primary nor fallback summary exists, FileNotFoundError is raised."""
    # Arrange
    monkeypatch.chdir(tmp_path)

    # Act & Assert
    with pytest.raises(FileNotFoundError, match="not found for language 'en'"):
        _load_summary("en")


# ---------------------------------------------------------------------------
# _load_or_extract_profile
# ---------------------------------------------------------------------------


def test_load_profile_from_json_when_json_exists(tmp_path, monkeypatch):
    """When data/user_profile.json exists and is non-empty, profile is loaded from JSON."""
    # Arrange
    monkeypatch.chdir(tmp_path)
    profile_dir = tmp_path / "data"
    profile_dir.mkdir(parents=True, exist_ok=True)
    json_path = profile_dir / "user_profile.json"
    json_path.write_text('{"_": "_"}', encoding="utf-8")

    mock_profile = MagicMock()

    with patch(
        "src.orchestrator.UserProfile.model_validate_json", return_value=mock_profile
    ) as mock_validate:
        # Act
        result = _load_or_extract_profile()

        # Assert
        assert result is mock_profile
        mock_validate.assert_called_once()


def test_load_profile_extracts_from_primary_md_when_no_json(tmp_path, monkeypatch):
    """When no JSON exists but data/background_md/ has .md files, extracts from primary."""
    # Arrange
    monkeypatch.chdir(tmp_path)
    bg_dir = tmp_path / "data" / "background_md"
    bg_dir.mkdir(parents=True, exist_ok=True)
    (bg_dir / "background_english.md").write_text("# Test", encoding="utf-8")

    mock_profile = MagicMock()

    with patch(
        "src.orchestrator.extract_profile_from_md", return_value=mock_profile
    ) as mock_extract:
        # Act
        result = _load_or_extract_profile()

        # Assert
        assert result is mock_profile
        mock_extract.assert_called_once()
        called_dir = mock_extract.call_args[0][0]
        expected_dir = str(Path("data/background_md"))
        assert called_dir == expected_dir, (
            f"Expected primary dir '{expected_dir}', got '{called_dir}'"
        )


def test_load_profile_falls_back_to_examples_when_primary_missing(tmp_path, monkeypatch):
    """When data/background_md/ is missing or empty, falls back to examples dir."""
    # Arrange
    monkeypatch.chdir(tmp_path)
    # Neither data/user_profile.json nor data/background_md/ exist

    mock_profile = MagicMock()

    with patch(
        "src.orchestrator.extract_profile_from_md", return_value=mock_profile
    ) as mock_extract:
        # Act
        result = _load_or_extract_profile()

        # Assert
        assert result is mock_profile
        mock_extract.assert_called_once()
        called_dir = mock_extract.call_args[0][0]
        assert called_dir == "examples/data/background_md/"
