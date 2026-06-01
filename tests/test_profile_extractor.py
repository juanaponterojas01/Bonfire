"""Integration tests for the profile extractor module (mocked LLM)."""

import json
import os
import tempfile

import pytest
from unittest.mock import patch

from src.models import UserProfile
from src.profile_extractor import extract_profile_from_md

MOCK_PROFILE_DICT = {
    "personal_info": {
        "name": "Juan Aponte",
        "address": "Braunschweig, Germany",
        "email": "juan@example.com",
        "phone": "+49 123 456789",
        "linkedin": None,
    },
    "education": [
        {
            "degree": "M.Sc. Mechanical Engineering",
            "institution": "TU Braunschweig",
            "subjects": ["Thermodynamics", "Fluid Mechanics", "Control Systems"],
            "thesis_title": "Optimal Control of a Charging Process for a Battery System",
            "year": "2024",
        }
    ],
    "experience": [
        {
            "name": "Internship at TLK-Thermo",
            "type": "industry",
            "role": "Intern",
            "duration": "Oct 2023 – Jan 2024",
            "key_contribution": "Developed Python backend software for data editing.",
            "technologies": ["Python", "Qt", "Sphinx"],
            "topics": ["programming", "thermal_simulation"],
        }
    ],
    "skills": [
        {"category": "software", "name": "Python", "proficiency": "advanced"},
        {"category": "technical", "name": "CFD", "proficiency": "intermediate"},
    ],
    "projects": [
        {
            "name": "Battery Charging Optimization",
            "type": "thesis",
            "role": "Researcher",
            "duration": "Apr 2024 – Oct 2024",
            "key_contribution": "Developed optimal control for battery charging.",
            "technologies": ["Modelica", "CasADi", "Python"],
            "topics": ["thermal_simulation", "thermodynamics", "programming"],
        }
    ],
}


@patch("src.profile_extractor.call_llm_parsed")
def test_extract_profile_reads_files_and_calls_llm(mock_call_llm_parsed):
    """Verify the extractor reads markdown files and calls the LLM with correct arguments."""
    mock_call_llm_parsed.return_value = UserProfile(**MOCK_PROFILE_DICT)

    with tempfile.TemporaryDirectory() as temp_dir:
        md_path = os.path.join(temp_dir, "test_bg.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("# Test Background\nSome content about Python development.")

        output_path = os.path.join(temp_dir, "user_profile.json")
        profile = extract_profile_from_md(temp_dir, output_path)

        assert mock_call_llm_parsed.call_count == 1
        _, kwargs = mock_call_llm_parsed.call_args
        assert "structured professional profile" in kwargs["system_prompt"]
        assert "Test Background" in kwargs["user_prompt"]
        assert kwargs["model"] == "deepseek-v4-flash"
        assert kwargs["response_model"] == UserProfile

        assert isinstance(profile, UserProfile)
        assert profile.personal_info.name == "Juan Aponte"

        assert os.path.exists(output_path)
        with open(output_path, "r", encoding="utf-8") as f:
            saved = json.load(f)
        assert saved["personal_info"]["name"] == "Juan Aponte"


def test_extract_profile_raises_on_empty_directory():
    """Verify FileNotFoundError is raised when no background markdown files exist."""
    with tempfile.TemporaryDirectory() as empty_dir:
        with pytest.raises(FileNotFoundError):
            extract_profile_from_md(empty_dir, "output.json")
