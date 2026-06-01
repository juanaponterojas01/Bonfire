"""Tests for the job evaluator module (mocked LLM)."""

from unittest.mock import patch

import pytest

from src.job_evaluator import (
    extract_job_description,
    extract_job_topics,
    evaluate_job_match,
)
from src.models import (
    Education,
    JobDescription,
    JobMatchResult,
    PersonalInfo,
    ProjectSummary,
    QualificationMatch,
    Skill,
    UserProfile,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

MOCK_PROFILE = UserProfile(
    personal_info=PersonalInfo(
        name="Juan Aponte",
        address="Braunschweig, Germany",
        email="juan@example.com",
        phone="+49 123 456789",
    ),
    education=[
        Education(
            degree="M.Sc. Mechanical Engineering",
            institution="TU Braunschweig",
            subjects=["Thermodynamics", "Fluid Mechanics"],
            year="2024",
        )
    ],
    experience=[
        ProjectSummary(
            name="Internship at TLK-Thermo",
            type="industry",
            role="Intern",
            duration="Oct 2023 – Jan 2024",
            key_contribution="Developed Python backend software.",
            technologies=["Python", "Qt"],
            topics=["programming", "thermal_simulation"],
        )
    ],
    skills=[
        Skill(category="software", name="Python", proficiency="advanced"),
        Skill(category="technical", name="CFD", proficiency="intermediate"),
    ],
    projects=[],
)

MOCK_JOB_TEXT = (
    "We are hiring a CFD engineer for our turbomachinery team. "
    "You will work on thermal simulation and fluid dynamics projects. "
    "Experience with programming and machine learning is a plus. "
    "Location: Munich, Germany. Company: AeroTech GmbH."
)


# ---------------------------------------------------------------------------
# extract_job_topics
# ---------------------------------------------------------------------------


@patch("src.job_evaluator.call_llm_parsed")
def test_extract_job_topics_returns_valid_topics(mock_call_llm_parsed):
    """Verify extract_job_topics returns the topics from the mocked LLM output."""
    mock_call_llm_parsed.return_value.topics = ["cfd", "thermal_simulation"]

    result = extract_job_topics(MOCK_JOB_TEXT)

    assert result == ["cfd", "thermal_simulation"]


@patch("src.job_evaluator.call_llm_parsed")
def test_extract_job_topics_filters_invalid(mock_call_llm_parsed):
    """Verify invalid/unrecognized topics are filtered out of the result."""
    mock_call_llm_parsed.return_value.topics = [
        "cfd",
        "made_up_topic",
        "thermal_simulation",
        "another_invalid",
    ]

    result = extract_job_topics(MOCK_JOB_TEXT)

    assert result == ["cfd", "thermal_simulation"]


# ---------------------------------------------------------------------------
# extract_job_description
# ---------------------------------------------------------------------------


@patch("src.job_evaluator.call_llm_parsed")
def test_extract_job_description_returns_job(mock_call_llm_parsed):
    """Verify extract_job_description returns a JobDescription with the expected fields."""
    mock_call_llm_parsed.return_value = JobDescription(
        title="CFD Engineer",
        company="AeroTech GmbH",
        location="Munich, Germany",
        raw_text="truncated by LLM",
        required_topics=["cfd", "thermal_simulation"],
    )

    result = extract_job_description(MOCK_JOB_TEXT)

    assert isinstance(result, JobDescription)
    assert result.title == "CFD Engineer"
    assert result.company == "AeroTech GmbH"
    assert result.location == "Munich, Germany"


@patch("src.job_evaluator.call_llm_parsed")
def test_extract_job_description_preserves_raw_text(mock_call_llm_parsed):
    """Verify the raw_text field is overwritten with the original job text."""
    mock_call_llm_parsed.return_value = JobDescription(
        title="CFD Engineer",
        company="AeroTech GmbH",
        location="Munich, Germany",
        raw_text="truncated by LLM",
        required_topics=["cfd"],
    )

    result = extract_job_description(MOCK_JOB_TEXT)

    assert result.raw_text == MOCK_JOB_TEXT


@patch("src.job_evaluator.call_llm_parsed")
def test_extract_job_description_filters_invalid_topics(mock_call_llm_parsed):
    """Verify required_topics are validated and invalid topics are stripped."""
    mock_call_llm_parsed.return_value = JobDescription(
        title="CFD Engineer",
        company="AeroTech GmbH",
        location="Munich, Germany",
        raw_text=MOCK_JOB_TEXT,
        required_topics=["cfd", "invalid_topic", "thermal_simulation"],
    )

    result = extract_job_description(MOCK_JOB_TEXT)

    assert result.required_topics == ["cfd", "thermal_simulation"]


# ---------------------------------------------------------------------------
# evaluate_job_match
# ---------------------------------------------------------------------------


@patch("src.job_evaluator.call_llm_parsed")
def test_evaluate_job_match_returns_result(mock_call_llm_parsed):
    """Verify evaluate_job_match returns the JobMatchResult from the mocked LLM."""
    expected = JobMatchResult(
        required_qualifications=[
            QualificationMatch(
                requirement="CFD experience",
                user_evidence="Internship at TLK-Thermo using CFD",
                match_level="strong",
            )
        ],
        gaps=["No machine learning experience"],
        strengths=["Strong Python skills"],
        recommendation="moderate_match",
        reasoning="Candidate has relevant CFD and Python experience.",
    )
    mock_call_llm_parsed.return_value = expected

    job = JobDescription(
        title="CFD Engineer",
        company="AeroTech GmbH",
        location="Munich, Germany",
        raw_text=MOCK_JOB_TEXT,
        required_topics=["cfd", "programming"],
    )

    result = evaluate_job_match(job, MOCK_PROFILE)

    assert result == expected


@patch("src.job_evaluator.call_llm_parsed")
def test_evaluate_job_match_passes_profile_and_job(mock_call_llm_parsed):
    """Verify the user prompt sent to the LLM includes job title and candidate name."""
    mock_call_llm_parsed.return_value = JobMatchResult(
        required_qualifications=[],
        gaps=[],
        strengths=[],
        recommendation="strong_match",
        reasoning="Good match.",
    )

    job = JobDescription(
        title="CFD Engineer",
        company="AeroTech GmbH",
        location="Munich, Germany",
        raw_text=MOCK_JOB_TEXT,
        required_topics=["cfd"],
    )

    evaluate_job_match(job, MOCK_PROFILE)

    _, kwargs = mock_call_llm_parsed.call_args

    assert kwargs["response_model"] == JobMatchResult
    assert kwargs["model"] == "deepseek-v4-flash"
    assert kwargs["temperature"] == 0.2

    user_prompt = kwargs["user_prompt"]
    assert "CFD Engineer" in user_prompt
    assert "Juan Aponte" in user_prompt


@patch("src.job_evaluator.call_llm_parsed")
def test_evaluate_job_match_user_prompt_includes_company_topics_and_json(
    mock_call_llm_parsed,
):
    """Verify the user prompt contains the company name, required topics,
    and the serialized profile JSON."""
    mock_call_llm_parsed.return_value = JobMatchResult(
        required_qualifications=[],
        gaps=[],
        strengths=[],
        recommendation="strong_match",
        reasoning="Good match.",
    )

    job = JobDescription(
        title="CFD Engineer",
        company="AeroTech GmbH",
        location="Munich, Germany",
        raw_text=MOCK_JOB_TEXT,
        required_topics=["cfd", "programming"],
    )

    evaluate_job_match(job, MOCK_PROFILE)

    _, kwargs = mock_call_llm_parsed.call_args
    user_prompt = kwargs["user_prompt"]

    assert "AeroTech GmbH" in user_prompt
    assert "cfd" in user_prompt
    assert "programming" in user_prompt
    # Profile JSON should contain key personal info and skill fields
    assert "Juan Aponte" in user_prompt
    assert "Python" in user_prompt
    assert '"name"' in user_prompt  # JSON key from model_dump_json


@patch("src.job_evaluator.call_llm_parsed")
def test_evaluate_job_match_passes_correct_system_prompt(mock_call_llm_parsed):
    """Verify the system prompt loaded from evaluate_job_match.md is passed to the LLM."""
    mock_call_llm_parsed.return_value = JobMatchResult(
        required_qualifications=[],
        gaps=[],
        strengths=[],
        recommendation="strong_match",
        reasoning="Good match.",
    )

    job = JobDescription(
        title="CFD Engineer",
        company="AeroTech GmbH",
        location="Munich, Germany",
        raw_text=MOCK_JOB_TEXT,
        required_topics=["cfd"],
    )

    evaluate_job_match(job, MOCK_PROFILE)

    _, kwargs = mock_call_llm_parsed.call_args
    system_prompt = kwargs["system_prompt"]

    assert "evaluating how well a candidate matches" in system_prompt
    assert "JobMatchResult" in system_prompt
