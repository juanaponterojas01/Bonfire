"""Tests for the DOCX cover letter generator (mocked file I/O)."""

from unittest.mock import MagicMock, patch

import pytest

from src.docx_generator import (
    _build_cover_letter_context,
    _replace_text_in_paragraph,
    render_cover_letter,
)
from src.models import JobDescription, PersonalInfo, UserProfile

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

MOCK_PROFILE = UserProfile(
    personal_info=PersonalInfo(
        name="Juan Aponte",
        address="Spinnerstra\u00dfe 35, 38114 Braunschweig",
        email="juan@example.com",
        phone="+49 123 456789",
        linkedin="https://linkedin.com/in/juan",
    ),
    education=[],
    experience=[],
    skills=[],
    projects=[],
)

MOCK_JOB = JobDescription(
    title="CFD Engineer",
    company="AeroTech GmbH",
    location="Munich, Germany",
    raw_text="We need a CFD engineer.",
    required_topics=["cfd"],
    receiver_name="Herr Dr. Mustermann",
)


# ---------------------------------------------------------------------------
# _replace_text_in_paragraph
# ---------------------------------------------------------------------------


def _make_paragraph(text: str) -> MagicMock:
    """Create a mock paragraph with a single run containing *text*."""
    paragraph = MagicMock()
    run = MagicMock()
    run.text = text
    paragraph.runs = [run]
    return paragraph


def _make_paragraph_with_runs(texts: list[str]) -> MagicMock:
    """Create a mock paragraph whose runs contain the given *texts*."""
    paragraph = MagicMock()
    paragraph.runs = []
    for t in texts:
        run = MagicMock()
        run.text = t
        paragraph.runs.append(run)
    return paragraph


def test_replace_text_in_paragraph_simple():
    """Verify a paragraph with a single run gets its text replaced correctly."""
    paragraph = _make_paragraph("Hello [name], welcome.")

    _replace_text_in_paragraph(paragraph, "[name]", "Juan")

    assert paragraph.runs[0].text == "Hello Juan, welcome."


def test_replace_text_in_paragraph_across_runs():
    """Verify a placeholder split across multiple runs is replaced correctly."""
    paragraph = _make_paragraph_with_runs(["[da", "te]", " rest"])

    _replace_text_in_paragraph(paragraph, "[date]", "04 May 2026")

    assert paragraph.runs[0].text == "04 May 2026 rest"
    assert paragraph.runs[1].text == ""
    assert paragraph.runs[2].text == ""


def test_replace_text_in_paragraph_no_match():
    """Verify paragraph text is unchanged when the placeholder is not present."""
    paragraph = _make_paragraph("Hello World, welcome.")

    _replace_text_in_paragraph(paragraph, "[name]", "Juan")

    assert paragraph.runs[0].text == "Hello World, welcome."


# ---------------------------------------------------------------------------
# _build_cover_letter_context
# ---------------------------------------------------------------------------


@patch("src.docx_generator.get_todays_date", return_value="04 May 2026")
def test_build_cover_letter_context(mock_get_date):
    """Verify the context dict has all 10 expected keys with correct values."""
    context = _build_cover_letter_context(
        MOCK_JOB, "Dear hiring manager...", "de", MOCK_PROFILE
    )

    expected_keys = {
        "[date]",
        "[company_name]",
        "[location]",
        "[greeting]",
        "[letter_body]",
        "[candidate_name]",
        "[candidate_address]",
        "[candidate_email]",
        "[candidate_phone]",
        "[candidate_linkedin]",
    }

    assert set(context.keys()) == expected_keys
    assert context["[date]"] == "04 May 2026"
    assert context["[company_name]"] == "AeroTech GmbH"
    assert context["[location]"] == "Munich, Germany"
    assert context["[greeting]"] == "Sehr geehrter Herr Dr. Mustermann,"
    assert context["[letter_body]"] == "Dear hiring manager..."
    assert context["[candidate_name]"] == "Juan Aponte"
    assert context["[candidate_address]"] == "Spinnerstraße 35, 38114 Braunschweig"
    assert context["[candidate_email]"] == "juan@example.com"
    assert context["[candidate_phone]"] == "+49 123 456789"
    assert context["[candidate_linkedin]"] == "https://linkedin.com/in/juan"
 


# ---------------------------------------------------------------------------
# render_cover_letter
# ---------------------------------------------------------------------------


@patch("src.docx_generator.Document")
@patch("src.docx_generator.Path.mkdir")
def test_render_cover_letter_creates_file(mock_mkdir, mock_Document):
    """Verify render_cover_letter loads the template, replaces placeholders, and saves the file."""
    mock_doc = MagicMock()
    mock_Document.return_value = mock_doc

    result = render_cover_letter(
        "template.docx", "output/test.docx",
        MOCK_JOB, "Dear Sir...", "de", MOCK_PROFILE
    )

    assert result == "output/test.docx"
    mock_doc.save.assert_called_once_with("output/test.docx")
    mock_mkdir.assert_called_once()

# if __name__ == "__main__":
#     test_render_cover_letter_creates_file()