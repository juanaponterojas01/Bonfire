"""Orchestrator that ties all Bonfire components into a single pipeline.

This module provides the main workflow engine. Given a job description and a
language, it loads the user profile, evaluates the job match, generates
tailored content, and renders the final application documents.
"""
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from src.models import JobDescription, UserProfile
from src.profile_extractor import extract_profile_from_md
from src.job_evaluator import extract_job_description
from src.content_writer import generate_cover_letter, generate_cv_dynamic_zones, generate_email_yaml
from src.context_selector import select_relevant_details
from src.docx_generator import render_cover_letter
from src.pptx_generator import render_cv
from src.utils import set_file_name
from src.job_history import log_job_entry


PROFILE_JSON_PATH = "data/user_profile.json"
BACKGROUND_SUMMARY_DIR = "data/background_md/"

_LANGUAGE_SUMMARY = {
    "de": "background_deutsch.md",
    "en": "background_english.md",
    "es": "background_español.md",
}


def _sanitize_company_name(name: str) -> str:
    """Sanitize a company name for use in a filesystem path.

    Replaces spaces with underscores and strips characters that are
    invalid or unsafe on common filesystems. Falls back to
    ``"unknown_company"`` if the result would otherwise be empty.
    """
    sanitized = name.replace(" ", "_")
    # Remove characters invalid on Windows and Unix
    sanitized = re.sub(r'[\\/:*?"<>|]', "", sanitized)
    sanitized = sanitized.strip("_-")
    return sanitized if sanitized else "unknown_company"


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
    source: str = "",
    profile: UserProfile | None = None,
) -> dict:
    """Execute job application steps pipeline.

    Loads or extracts the user profile (if not provided), parses the job
    description, generates tailored cover letter, CV content, and
    application email, then renders the final documents.

    Args:
        job_text: The raw text of the job posting.
        language: Language code for generated content (``"en"``, ``"de"``, ``"es"``).
        source:   URL or file path from which the job was obtained.
                  Defaults to ``""``. When non-empty, the job is
                  automatically logged to ``data/job-history.csv``
                  with state ``"pending"``.
        profile:  An optional pre-loaded :class:`UserProfile`. If ``None``,
                  the profile is loaded from disk (``data/user_profile.json``
                  or extracted from Markdown files).

    Returns:
        A dictionary with ``"success": True`` and output file paths
        (``"cover_letter"``, ``"cv"``, ``"email"``) on success, or
        ``"success": False`` with a ``"reason"`` on failure.
    """
    try:
        print("loading and parsing job description, and reading background...\n")
        with ThreadPoolExecutor(max_workers=3) as executor:
            if profile is None:
                future_profile = executor.submit(_load_or_extract_profile)
            future_job = executor.submit(_parse_job_description, job_text)
            future_summary = executor.submit(_load_summary, language)

            if profile is None:
                profile = future_profile.result()
            job = future_job.result()
            if source:
                log_job_entry(job, source=source, state="pending")
            raw_background_text = future_summary.result()
            relevant_details = select_relevant_details(
                job=job,
                profile=profile,
                background_text=raw_background_text,
            )

        # Phase 2: Cover letter and CV zones run concurrently
        print("Generating cover letter, CV dynamic zones, and email...\n")
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_letter = executor.submit(
                generate_cover_letter, job, profile, relevant_details, language
            )
            future_cv = executor.submit(
                generate_cv_dynamic_zones, job, profile, language
            )
            future_email = executor.submit(
                generate_email_yaml, job, profile, language
            )

            letter_body = future_letter.result()
            dynamic_zones = future_cv.result()
            email_yaml_content = future_email.result()

        timestamp = int(time.time() * 1_000_000)
        sanitized_company = _sanitize_company_name(job.company)
        output_dir = Path("output") / f"{sanitized_company}_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)

        print("Creating email...\n")
        email_path = output_dir / "email.yaml"
        email_path.write_text(email_yaml_content, encoding="utf-8")

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
            "email": str(email_path),
        }

    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:
        return {"success": False, "reason": str(e)}