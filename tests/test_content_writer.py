"""Tests for the content writer module (mocked LLM)."""
from unittest.mock import patch

import pytest

from src.content_writer import (
    generate_cover_letter,
    generate_cv_dynamic_zones,
    generate_email_yaml,
)
from src.config import CONFIG
from src.models import (
    CVDynamicZones,
    Education,
    JobDescription,
    PersonalInfo,
    ProjectSummary,
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
    projects=[
        ProjectSummary(
            name="Battery Charging Optimization",
            type="thesis",
            role="Researcher",
            duration="Apr 2024 – Oct 2024",
            key_contribution="Developed optimal control for battery charging.",
            technologies=["Modelica", "CasADi", "Python"],
            topics=["thermal_simulation", "thermodynamics", "programming"],
        )
    ],
)

MOCK_JOB = JobDescription(
    title="CFD Engineer",
    company="AeroTech GmbH",
    location="Munich, Germany",
    raw_text="We are hiring a CFD engineer for our turbomachinery team.",
    required_topics=["cfd", "thermal_simulation"],
)

MOCK_RELEVANT_DETAILS = "Detailed CFD analysis of turbine blades."

# ---------------------------------------------------------------------------
# generate_cover_letter
# ---------------------------------------------------------------------------


@patch("src.content_writer.call_llm")
def test_generate_cover_letter_returns_string(mock_call_llm):
    """Verify generate_cover_letter returns a string from the mocked LLM."""
    mock_call_llm.return_value = "Dear Hiring Manager..."

    result = generate_cover_letter(MOCK_JOB, MOCK_PROFILE, MOCK_RELEVANT_DETAILS, "en")

    assert isinstance(result, str)


@patch("src.content_writer.call_llm")
def test_generate_cover_letter_passes_correct_args(mock_call_llm):
    """Verify the LLM is called with the correct model, temperature, and prompt content."""
    mock_call_llm.return_value = "letter text"

    generate_cover_letter(MOCK_JOB, MOCK_PROFILE, MOCK_RELEVANT_DETAILS, "en")

    _, kwargs = mock_call_llm.call_args

    assert kwargs["model"] == CONFIG.models.writer_model
    assert kwargs["temperature"] == CONFIG.settings.temperature_writing

    user_prompt = kwargs["user_prompt"]
    assert "CFD Engineer" in user_prompt

    system_prompt = kwargs["system_prompt"]
    assert "Juan Aponte" in system_prompt


@patch("src.content_writer.call_llm")
def test_generate_cover_letter_includes_language_in_prompt(mock_call_llm):
    """Verify the system prompt contains the language string (e.g., 'in de')."""
    mock_call_llm.return_value = "letter"

    generate_cover_letter(MOCK_JOB, MOCK_PROFILE, MOCK_RELEVANT_DETAILS, "de")

    _, kwargs = mock_call_llm.call_args

    system_prompt = kwargs["system_prompt"]
    assert "in german" in system_prompt

# ---------------------------------------------------------------------------
# generate_email_yaml
# ---------------------------------------------------------------------------


@patch("src.content_writer.call_llm")
def test_generate_email_yaml_returns_string(mock_call_llm):
    """Verify generate_email_yaml returns a string from the mocked LLM."""
    mock_call_llm.return_value = "subject: Application to CFD Engineer..."

    result = generate_email_yaml(MOCK_JOB, MOCK_PROFILE, "en")

    assert isinstance(result, str)


@patch("src.content_writer.call_llm")
def test_generate_email_yaml_passes_correct_args(mock_call_llm):
    """Verify the LLM is called with the correct model, temperature, and prompt content."""
    mock_call_llm.return_value = "email yaml text"

    generate_email_yaml(MOCK_JOB, MOCK_PROFILE, "en")

    _, kwargs = mock_call_llm.call_args

    assert kwargs["model"] == CONFIG.models.writer_model
    assert kwargs["temperature"] == CONFIG.settings.temperature_writing

    user_prompt = kwargs["user_prompt"]
    assert "CFD Engineer" in user_prompt
    assert "AeroTech GmbH" in user_prompt

    system_prompt = kwargs["system_prompt"]
    assert "Juan Aponte" in system_prompt


@patch("src.content_writer.call_llm")
def test_generate_email_yaml_includes_format_in_prompt(mock_call_llm):
    """Verify the system prompt contains key YAML format elements."""
    mock_call_llm.return_value = "formatted email yaml"

    generate_email_yaml(MOCK_JOB, MOCK_PROFILE, "en")

    _, kwargs = mock_call_llm.call_args

    system_prompt = kwargs["system_prompt"]
    assert "subject:" in system_prompt
    assert "to:" in system_prompt
    assert "maximum 90 words" in system_prompt
    assert "GREETING RULES" in system_prompt
    assert "Farewell" in system_prompt


@patch("src.content_writer.call_llm")
def test_generate_email_yaml_includes_rules_in_prompt(mock_call_llm):
    """Verify the system prompt contains the required rule constraints."""
    mock_call_llm.return_value = "email with rules"

    generate_email_yaml(MOCK_JOB, MOCK_PROFILE, "en")

    _, kwargs = mock_call_llm.call_args

    system_prompt = kwargs["system_prompt"]
    assert "Do NOT invent" in system_prompt
    assert "Do NOT use generic phrases" in system_prompt
    assert "PRE-OUTPUT VERIFICATION CHECKLIST" in system_prompt
