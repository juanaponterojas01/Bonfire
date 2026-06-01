"""Tests for the orchestrator pipeline (mocked LLM and file I/O)."""

from pathlib import Path
from unittest.mock import patch

from src.models import (
    CVDynamicZones,
    JobDescription,
    PersonalInfo,
    UserProfile,
)
from src.orchestrator import run_job_pipeline


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_profile() -> UserProfile:
    """Create a minimal UserProfile for testing."""
    return UserProfile(
        personal_info=PersonalInfo(
            name="Juan Aponte",
            address="123 Main St",
            email="juan@example.com",
            phone="+1234567890",
        ),
        education=[],
        experience=[],
        skills=[],
        projects=[],
    )


def _make_job() -> JobDescription:
    """Create a minimal JobDescription for testing."""
    return JobDescription(
        title="CFD Engineer",
        company="AeroTech GmbH",
        location="Munich, Germany",
        raw_text="We are hiring a CFD engineer.",
        required_topics=["cfd"],
    )


def _make_cv_zones() -> CVDynamicZones:
    """Create minimal CVDynamicZones for testing."""
    return CVDynamicZones(
        professional_summary="Experienced engineer.",
        bachelor_subjects="Fluid Mechanics, Thermodynamics",
        master_subjects="Advanced CFD, Turbulence Modeling",
    )


# ---------------------------------------------------------------------------
# Test 1: context selector receives correct arguments
# ---------------------------------------------------------------------------


@patch.object(Path, "write_text")
@patch.object(Path, "mkdir")
@patch("src.orchestrator._load_or_extract_profile")
@patch("src.orchestrator.extract_job_description")
@patch("src.orchestrator._load_summary")
@patch("src.orchestrator.select_relevant_details")
@patch("src.orchestrator.generate_cover_letter")
@patch("src.orchestrator.generate_cv_dynamic_zones")
@patch("src.orchestrator.generate_email_yaml")
@patch("src.orchestrator.render_cover_letter")
@patch("src.orchestrator.render_cv")
def test_pipeline_calls_context_selector_with_correct_args(
    mock_render_cv,
    mock_render_letter,
    mock_gen_email,
    mock_gen_cv,
    mock_gen_letter,
    mock_select,
    mock_summary,
    mock_parse_job,
    mock_load_profile,
    mock_mkdir,
    mock_write_text,
):
    """Verify select_relevant_details receives the correct job, profile, and
    background_text from the pipeline."""
    # Arrange
    profile = _make_profile()
    job = _make_job()
    cv_zones = _make_cv_zones()

    mock_load_profile.return_value = profile
    mock_parse_job.return_value = job
    mock_summary.return_value = "raw background text"
    mock_select.return_value = "filtered context"
    mock_gen_letter.return_value = "Dear Sir..."
    mock_gen_cv.return_value = cv_zones
    mock_gen_email.return_value = "subject: Application..."
    mock_render_letter.return_value = "output/AeroTech GmbH/cover_letter.docx"
    mock_render_cv.return_value = "output/AeroTech GmbH/cv.pptx"

    # Act
    run_job_pipeline("some job text", "en")

    # Assert
    mock_select.assert_called_once_with(
        job=job,
        profile=profile,
        background_text="raw background text",
    )


# ---------------------------------------------------------------------------
# Test 2: content generators receive filtered context, not raw text
# ---------------------------------------------------------------------------


@patch.object(Path, "write_text")
@patch.object(Path, "mkdir")
@patch("src.orchestrator._load_or_extract_profile")
@patch("src.orchestrator.extract_job_description")
@patch("src.orchestrator._load_summary")
@patch("src.orchestrator.select_relevant_details")
@patch("src.orchestrator.generate_cover_letter")
@patch("src.orchestrator.generate_cv_dynamic_zones")
@patch("src.orchestrator.generate_email_yaml")
@patch("src.orchestrator.render_cover_letter")
@patch("src.orchestrator.render_cv")
def test_relevant_details_not_raw_full_text(
    mock_render_cv,
    mock_render_letter,
    mock_gen_email,
    mock_gen_cv,
    mock_gen_letter,
    mock_select,
    mock_summary,
    mock_parse_job,
    mock_load_profile,
    mock_mkdir,
    mock_write_text,
):
    """Verify generate_cover_letter receives the filtered context from
    select_relevant_details, not the raw background text."""
    # Arrange
    profile = _make_profile()
    job = _make_job()
    cv_zones = _make_cv_zones()

    mock_load_profile.return_value = profile
    mock_parse_job.return_value = job
    mock_summary.return_value = "raw background text"
    mock_select.return_value = "filtered context"
    mock_gen_letter.return_value = "Dear Sir..."
    mock_gen_cv.return_value = cv_zones
    mock_gen_email.return_value = "subject: Application..."
    mock_render_letter.return_value = "output/AeroTech GmbH/cover_letter.docx"
    mock_render_cv.return_value = "output/AeroTech GmbH/cv.pptx"

    # Act
    run_job_pipeline("some job text", "en")

    # Assert
    mock_gen_letter.assert_called_once_with(
        job, profile, "filtered context", "en"
    )


# ---------------------------------------------------------------------------
# Test 3: successful pipeline returns expected structure
# ---------------------------------------------------------------------------


@patch.object(Path, "write_text")
@patch.object(Path, "mkdir")
@patch("src.orchestrator._load_or_extract_profile")
@patch("src.orchestrator.extract_job_description")
@patch("src.orchestrator._load_summary")
@patch("src.orchestrator.select_relevant_details")
@patch("src.orchestrator.generate_cover_letter")
@patch("src.orchestrator.generate_cv_dynamic_zones")
@patch("src.orchestrator.generate_email_yaml")
@patch("src.orchestrator.render_cover_letter")
@patch("src.orchestrator.render_cv")
def test_pipeline_success(
    mock_render_cv,
    mock_render_letter,
    mock_gen_email,
    mock_gen_cv,
    mock_gen_letter,
    mock_select,
    mock_summary,
    mock_parse_job,
    mock_load_profile,
    mock_mkdir,
    mock_write_text,
):
    """Verify the full pipeline returns a success dict with all required keys."""
    # Arrange
    profile = _make_profile()
    job = _make_job()
    cv_zones = _make_cv_zones()

    mock_load_profile.return_value = profile
    mock_parse_job.return_value = job
    mock_summary.return_value = "raw background text"
    mock_select.return_value = "filtered context"
    mock_gen_letter.return_value = "Dear Sir..."
    mock_gen_cv.return_value = cv_zones
    mock_gen_email.return_value = "subject: Application..."
    mock_render_letter.return_value = "output/AeroTech GmbH/cover_letter.docx"
    mock_render_cv.return_value = "output/AeroTech GmbH/cv.pptx"

    # Act
    result = run_job_pipeline("some job text", "en")

    # Assert
    assert result["success"] is True
    assert result["company"] == "AeroTech GmbH"
    assert result["job_title"] == "CFD Engineer"
    assert "AeroTech" in result["output_dir"]
    assert "output" in result["output_dir"]
    assert result["cover_letter"] == "output/AeroTech GmbH/cover_letter.docx"
    assert result["cv"] == "output/AeroTech GmbH/cv.pptx"
    assert "email" in result


# ---------------------------------------------------------------------------
# Test 4: pipeline failure returns error dict
# ---------------------------------------------------------------------------


@patch("src.orchestrator._load_or_extract_profile")
@patch("src.orchestrator.extract_job_description")
@patch("src.orchestrator._load_summary")
def test_pipeline_failure(
    mock_summary,
    mock_parse_job,
    mock_load_profile,
):
    """Verify a RuntimeError during job parsing yields failure dict with reason."""
    # Arrange
    mock_load_profile.return_value = _make_profile()
    mock_parse_job.side_effect = RuntimeError("LLM failed")
    mock_summary.return_value = "raw background text"

    # Act
    result = run_job_pipeline("some job text", "en")

    # Assert
    assert result == {"success": False, "reason": "LLM failed"}


# ---------------------------------------------------------------------------
# Test 5: job is logged when source URL is provided
# ---------------------------------------------------------------------------


@patch.object(Path, "write_text")
@patch.object(Path, "mkdir")
@patch("src.orchestrator._load_or_extract_profile")
@patch("src.orchestrator.extract_job_description")
@patch("src.orchestrator._load_summary")
@patch("src.orchestrator.select_relevant_details")
@patch("src.orchestrator.generate_cover_letter")
@patch("src.orchestrator.generate_cv_dynamic_zones")
@patch("src.orchestrator.generate_email_yaml")
@patch("src.orchestrator.render_cover_letter")
@patch("src.orchestrator.render_cv")
@patch("src.orchestrator.log_job_entry")
def test_pipeline_logs_job_when_source_provided(
    mock_log_job,
    mock_render_cv,
    mock_render_letter,
    mock_gen_email,
    mock_gen_cv,
    mock_gen_letter,
    mock_select,
    mock_summary,
    mock_parse_job,
    mock_load_profile,
    mock_mkdir,
    mock_write_text,
):
    """Verify log_job_entry is called with the parsed job when a source URL is
    provided."""
    # Arrange
    profile = _make_profile()
    job = _make_job()
    cv_zones = _make_cv_zones()

    mock_load_profile.return_value = profile
    mock_parse_job.return_value = job
    mock_summary.return_value = "raw background text"
    mock_select.return_value = "filtered context"
    mock_gen_letter.return_value = "Dear Sir..."
    mock_gen_cv.return_value = cv_zones
    mock_gen_email.return_value = "subject: Application..."
    mock_render_letter.return_value = "output/AeroTech GmbH/cover_letter.docx"
    mock_render_cv.return_value = "output/AeroTech GmbH/cv.pptx"

    # Act
    run_job_pipeline("job text", "en", source="https://example.com/job")

    # Assert
    mock_log_job.assert_called_once_with(
        job, source="https://example.com/job", state="pending"
    )
