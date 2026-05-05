"""Orchestrator that ties all Bonfire components into a single pipeline.

This module provides the main workflow engine. Given a job description and a
language, it loads the user profile, evaluates the job match, generates
tailored content, validates it, and renders the final application documents.
"""
import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.models import JobDescription, UserProfile
from src.profile_extractor import extract_profile_from_md
from src.job_evaluator import extract_job_description
from src.content_writer import generate_cover_letter, generate_cv_dynamic_zones
from src.content_validator import validate_content
from src.docx_generator import render_cover_letter
from src.pptx_generator import render_cv
from src.utils import set_file_name


PROFILE_JSON_PATH = "data/user_profile.json"
BACKGROUND_SUMMARY_DIR = "data/background_md/"

_LANGUAGE_SUMMARY = {
    "de": "background_deutsch.md",
    "en": "background_english.md",
    "es": "background_español.md",
}


def _load_or_extract_profile() -> UserProfile:
    """Load the user profile from JSON or extract it from Markdown files.

    Checks whether ``data/user_profile.json`` exists and is non-empty. If so,
    it is parsed into a :class:`UserProfile`. Otherwise the profile is
    extracted from the background Markdown directory and persisted to the
    same JSON path.

    Returns:
        The validated :class:`UserProfile` instance.
    """
    profile_path = Path(PROFILE_JSON_PATH)
    if profile_path.exists() and profile_path.stat().st_size > 0:
        return UserProfile.model_validate_json(profile_path.read_text(encoding="utf-8"))

    return extract_profile_from_md(BACKGROUND_SUMMARY_DIR, PROFILE_JSON_PATH)


def _load_summary(language: str) -> str:
    """Load the language-specific background summary from ``data/summary/``.

    Args:
        language: Language code (``"en"``, ``"de"``, or ``"es"``).

    Returns:
        The full text content of the corresponding summary file.

    Raises:
        FileNotFoundError: If the summary file for the language does not exist.
        KeyError: If *language* is not supported.
    """
    file_name = _LANGUAGE_SUMMARY[language]
    summary_path = Path.cwd()/Path(BACKGROUND_SUMMARY_DIR) / file_name
    return summary_path.read_text(encoding="utf-8")


def _parse_job_description(job_text: str) -> JobDescription:
    """Parse a raw job posting into a structured :class:`JobDescription`.

    Args:
        job_text: The raw text of the job posting.

    Returns:
        A validated :class:`JobDescription` with all fields populated.
    """
    return extract_job_description(job_text)

def run_job_pipeline(
    job_text: str,
    language: str,
) -> dict:
    """Execute job application steps pipeline.

    Loads or extracts the user profile, parses the job description, 
    generates tailored cover letter and CV content, validates the
    output, and renders the final documents.

    Args:
        job_text: The raw text of the job posting.
        language: Language code for generated content (``"en"``, ``"de"``, ``"es"``).
        

    Returns:
        A dictionary with ``"success": True`` and output file paths on
        success, or ``"success": False`` with a ``"reason"`` on failure.
    """
    try:
        print("loading and parsing job description...\n")
        profile = _load_or_extract_profile()
        job = _parse_job_description(job_text)

        print("Reading background...\n")
        relevant_details = _load_summary(language)

        print("Genearating cover letter...\n")
        letter_body = generate_cover_letter(job, profile, relevant_details, language)

        flags = validate_content(letter_body, profile)
        if flags:
            print(
                f"Warning: Cover letter validation flagged {len(flags)} claims: {flags}",
                file=sys.stderr,
            )

        print("Generating cv dynamic zones...\n")
        dynamic_zones = generate_cv_dynamic_zones(job, profile, language)

        output_dir = Path("output") / job.company
        output_dir.mkdir(parents=True, exist_ok=True)

        print("Creating cover letter...\n")
        cover_letter_path = render_cover_letter(
            template_path=f"templates/{language}/cover_letter_template.docx",
            output_path=str(output_dir / set_file_name("motiv_letter", language, profile.personal_info)),
            job=job,
            letter_body=letter_body,
            language=language,
        )
        print("Creating cv ...\n")
        cv_path = render_cv(
            template_path=f"templates/{language}/cv_template.pptx",
            output_path=str(output_dir / set_file_name("curriculum", language, profile.personal_info)),
            job=job,
            profile=profile,
            dynamic_zones=dynamic_zones,
            language=language,
        )

        return {
            "success": True,
            "company": job.company,
            "job_title": job.title,
            "output_dir": str(output_dir),
            "cover_letter": cover_letter_path,
            "cv": cv_path,
        }

    except Exception as e:
        return {"success": False, "reason": str(e)}


if __name__ == "__main__":

     _load_summary("de")