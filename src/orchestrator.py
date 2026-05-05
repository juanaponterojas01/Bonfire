"""Orchestrator that ties all Bonfire components into a single pipeline.

This module provides the main workflow engine. Given a job description and a
language, it loads the user profile, evaluates the job match, generates
tailored content, validates it, and renders the final application documents.
"""

import sys
from pathlib import Path

from src.models import JobDescription, JobMatchResult, UserProfile
from src.profile_extractor import extract_profile_from_md
from src.job_evaluator import extract_job_description, evaluate_job_match
from src.content_writer import generate_cover_letter, generate_cv_dynamic_zones
from src.content_validator import validate_content
from src.docx_generator import render_cover_letter
from src.pptx_generator import render_cv
from src.utils import set_file_name


PROFILE_JSON_PATH = "data/user_profile.json"
BACKGROUND_MD_DIR = "data/background_md/"
SUMMARY_DIR = Path("data/summary")

_LANGUAGE_SUMMARY = {
    "de": "background_zusammenfassung.md",
    "en": "background_summary.md",
    "es": "background_resumen.md",
}

_THRESHOLD_LEVELS = {
    "weak_match": 0,
    "moderate_match": 1,
    "strong_match": 2,
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

    return extract_profile_from_md(BACKGROUND_MD_DIR, PROFILE_JSON_PATH)


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
    summary_path = SUMMARY_DIR / file_name
    return summary_path.read_text(encoding="utf-8")


def _parse_job_description(job_text: str) -> JobDescription:
    """Parse a raw job posting into a structured :class:`JobDescription`.

    Args:
        job_text: The raw text of the job posting.

    Returns:
        A validated :class:`JobDescription` with all fields populated.
    """
    return extract_job_description(job_text)


def _check_threshold(result: JobMatchResult, threshold: str) -> bool:
    """Check whether a match result meets or exceeds the given threshold.

    Uses ordinal threshold levels where ``strong_match`` > ``moderate_match``
    > ``weak_match``.

    Args:
        result: The job match result containing a ``recommendation`` field.
        threshold: The minimum acceptable recommendation level.

    Returns:
        ``True`` if the result's recommendation is at or above the threshold,
        ``False`` otherwise.
    """
    result_level = _THRESHOLD_LEVELS.get(result.recommendation, -1)
    threshold_level = _THRESHOLD_LEVELS.get(threshold, 1)
    return result_level >= threshold_level


def run_job_pipeline(
    job_text: str,
    language: str,
    compatibility_threshold: str = "moderate_match",
) -> dict:
    """Execute the full 12-step job application pipeline.

    Loads or extracts the user profile, parses the job description, evaluates
    the match, generates tailored cover letter and CV content, validates the
    output, and renders the final documents.

    Args:
        job_text: The raw text of the job posting.
        language: Language code for generated content (``"en"``, ``"de"``, ``"es"``).
        compatibility_threshold: Minimum match level to proceed. One of
            ``"weak_match"``, ``"moderate_match"``, or ``"strong_match"``.
            Defaults to ``"moderate_match"``.

    Returns:
        A dictionary with ``"success": True`` and output file paths on
        success, or ``"success": False`` with a ``"reason"`` on failure.
    """
    try:
        print("loading and parsing job description...\n")
        profile = _load_or_extract_profile()
        job = _parse_job_description(job_text)
        match_result = evaluate_job_match(job, profile)

        if not _check_threshold(match_result, compatibility_threshold):
            return {
                "success": False,
                "reason": "Job mismatch",
                "recommendation": match_result.recommendation,
            }

        print("Read background...\n")
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
            profile=profile,
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
            "recommendation": match_result.recommendation,
            "output_dir": str(output_dir),
            "cover_letter": cover_letter_path,
            "cv": cv_path,
        }

    except Exception as e:
        return {"success": False, "reason": str(e)}
