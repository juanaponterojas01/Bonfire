"""Generate AI-written content for cover letters, emails, and CV dynamic zones.

This module generates the creative text that fills the dynamic sections of job
application documents. It uses the raw-text LLM path for the cover letter body
and the application email, and the structured-output path for the CV zones that
must conform to the :class:`CVDynamicZones` schema.
"""

import json

from src.llm_client import call_llm, call_llm_parsed
from src.config import CONFIG
from src.models import CVDynamicZones, JobDescription, UserProfile
from src.utils import render_prompt

_LANGUAGE_COUNTRY = {
    "en": "Europe",
    "de": "Germany",
    "es": "Colombia",
}

_LANGUAGE_MAPPING = {
    "en": "english",
    "de": "german",
    "es": "spanish",
}

def generate_cover_letter(
    job: JobDescription,
    profile: UserProfile,
    relevant_details: str,
    language: str,
) -> str:
    """Generate a tailored motivation letter for a job application.

    Constructs a four-paragraph cover letter structured around interest in
    the specific position, evidence-driven experience claims, differentiators,
    and a professional closing. The prompt includes the full job description,
    the candidate profile as JSON, and pre-extracted evidence so that every
    claim is grounded in real background information. The tone is matched to
    the country associated with *language* via the ``_LANGUAGE_COUNTRY``
    mapping.

    This function uses the raw-text LLM path (:func:`call_llm` with the
    :data:`WRITER_MODEL`) to produce free-form prose.

    Args:
        job: The target job description.
        profile: The candidate's full profile.
        relevant_details: Pre-extracted evidence to support specific claims.
        language: Language code for the letter (``"en"``, ``"de"``, or ``"es"``).

    Returns:
        The raw text of the generated cover letter body.

    Raises:
        KeyError: If *language* is not a key in ``_LANGUAGE_COUNTRY``.
        ValueError: If the ``OPENCODE_API_KEY`` environment variable is not set.
        RuntimeError: If the LLM call fails.
    """
    text_language = _LANGUAGE_MAPPING[language]
    country = _LANGUAGE_COUNTRY[language]
    profile_summary = json.dumps(
        profile.model_dump(), indent=2, ensure_ascii=False
    )

    system_prompt = render_prompt(
        "cover_letter",
        text_language=text_language,
        job_raw_text=job.raw_text,
        profile_summary=profile_summary,
        relevant_details=relevant_details,
        country=country,
    )

    user_prompt = (
        f"Write the motivation letter for the position of {job.title} "
        f"at {job.company}."
    )

    return call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=CONFIG.models.writer_model,
        temperature=CONFIG.settings.temperature_writing,
        max_tokens=CONFIG.settings.max_tokens_writing,
    )

def generate_cv_dynamic_zones(
    job: JobDescription,
    profile: UserProfile,
    language: str,
) -> CVDynamicZones:
    """Generate dynamic CV content zones tailored to a specific job.

    Produces the structured content that fills the dynamic sections of a
    CV: a three-sentence professional summary, one sentence explaining the user's relevant
    bachelor subjects, and one sentence explaining the user's relevant master subjects.

    This function uses the structured-output LLM path
    (:func:`call_llm_parsed`) to obtain a validated
    :class:`CVDynamicZones` instance directly from the model response.

    Args:
        job: The target job description.
        profile: The candidate's full profile.
        language: Language code for the content (``"en"``, ``"de"``, or ``"es"``).

    Returns:
        A validated :class:`CVDynamicZones` instance with all generated content.

    Raises:
        ValueError: If the LLM response cannot be parsed as valid JSON
            matching the schema after exhausting all retries.
        RuntimeError: If the underlying LLM call fails.
    """
    text_language = _LANGUAGE_MAPPING[language]

    # Slim profile with only fields relevant to CV dynamic zones
    relevant_profile = {
        "education": [edu.model_dump() for edu in profile.education],
        "skills": [skill.model_dump() for skill in profile.skills],
        "experience": [
            {"name": exp.name, "role": exp.role, "topics": exp.topics}
            for exp in profile.experience
        ],
        "projects": [
            {"name": p.name, "topics": p.topics}
            for p in profile.projects
        ],
    }
    profile_json = json.dumps(relevant_profile, indent=2, ensure_ascii=False)

    system_prompt = render_prompt(
        "cv_dynamic_zones",
        text_language=text_language,
        job_title=job.title,
        company=job.company,
        required_topics=", ".join(job.required_topics),
        profile_evidence=profile_json,
    )

    user_prompt = (
        f"JOB TITLE: {job.title}\n"
        f"COMPANY: {job.company}\n"
        f"LOCATION: {job.location}\n"
        f"REQUIRED TOPICS: {', '.join(job.required_topics)}\n"
        "\n"
        f"JOB DESCRIPTION:\n{job.raw_text}\n"
        "\n"
        f"CANDIDATE PROFILE:\n{profile_json}"
    )

    return call_llm_parsed(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_model=CVDynamicZones,
        model=CONFIG.models.extraction_model,
        temperature=CONFIG.settings.temperature_extraction,
        max_tokens=CONFIG.settings.max_tokens_extraction,
        timeout=CONFIG.settings.timeout,
    )


def generate_email_yaml(
    job: JobDescription,
    profile: UserProfile,
    language: str,
) -> str:
    """Generate a short, direct application email for a job posting.

    Produces a concise, professional email including a YAML-style preamble
    (``subject:`` and ``to:`` fields), a greeting, a body paragraph, and a
    farewell. The email is written entirely in the language specified by
    the *language* parameter.

    This function uses the raw-text LLM path (:func:`call_llm` with the
    :data:`WRITER_MODEL`) to produce free-form prose.

    Args:
        job (JobDescription): The target job description. Uses ``title``,
            ``company``, ``email``, and ``raw_text``.
        profile (UserProfile): The candidate's full profile. Uses
            ``personal_info.name`` and qualifications to ground claims.
        language (str): Language code that determines the target language
            for the email (``"en"``, ``"de"``, or ``"es"``). The LLM uses
            this to write the entire email in that language.

    Returns:
        str: The raw text of the generated email, beginning with
        YAML-style ``subject:`` and ``to:`` fields, followed by the
        greeting, body, and farewell.

    Raises:
        KeyError: If *language* is not a key in ``_LANGUAGE_MAPPING``.
        ValueError: If the ``OPENCODE_API_KEY`` environment variable is not
            set.
        RuntimeError: If the LLM call fails.
    """
    text_language = _LANGUAGE_MAPPING[language]
    profile_json = json.dumps(
        profile.model_dump(), indent=2, ensure_ascii=False
    )

    system_prompt = render_prompt(
        "email_yaml",
        text_language=text_language,
        job_raw_text=job.raw_text,
        profile_json=profile_json,
        job_title=job.title,
        job_email=job.email,
        candidate_name=profile.personal_info.name,
        company=job.company,
        receiver_name=job.receiver_name,
    )

    user_prompt = (
        f"Write the email for the position of {job.title} "
        f"at {job.company}."
    )

    return call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=CONFIG.models.writer_model,
        temperature=CONFIG.settings.temperature_writing,
        max_tokens=CONFIG.settings.max_tokens_writing,
    )

