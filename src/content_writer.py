"""Generate AI-written content for cover letters and CV dynamic zones.

This module generates the creative text that fills the dynamic sections of job
application documents. It uses the raw-text LLM path for the cover letter body
and the structured-output path for the CV zones that must conform to the
:class:`CVDynamicZones` schema.
"""

import json

from src.llm_client import call_llm, call_llm_parsed, WRITER_MODEL
from src.models import CVDynamicZones, JobDescription, UserProfile

_LANGUAGE_COUNTRY = {
    "en": "the United States",
    "de": "Germany",
    "es": "Spain",
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
    country = _LANGUAGE_COUNTRY[language]
    profile_summary = json.dumps(
        profile.model_dump(), indent=2, ensure_ascii=False
    )

    system_prompt = (
        f"Write a motivation letter in {language} for the following position.\n"
        "\n"
        f"JOB DESCRIPTION:\n{job.raw_text}\n"
        "\n"
        f"CANDIDATE PROFILE:\n{profile_summary}\n"
        "\n"
        f"DETAILED EVIDENCE (use these to support specific claims):\n"
        f"{relevant_details}\n"
        "\n"
        "STRUCTURE REQUIREMENTS:\n"
        "- Paragraph 1: Express interest in the specific position and company. "
        "Reference something specific about the company or role that attracts you.\n"
        "- Paragraph 2: Connect your experience to their requirements. "
        "Cite specific projects or achievements as evidence.\n"
        "- Paragraph 3: Highlight what makes you a strong candidate beyond "
        "the basic requirements.\n"
        "- Paragraph 4: Express enthusiasm for an interview. Professional closing.\n"
        "\n"
        "RULES:\n"
        "- Do NOT invent qualifications, experiences, or achievements not "
        "present in the profile or evidence\n"
        "- Do NOT use generic phrases like \"I am writing to apply for\" or "
        "\"I believe I am an ideal candidate\"\n"
        "- Be specific and concrete \u2014 every claim should reference "
        "something real from the background\n"
        f"- Match the tone expected in {country}'s job market\n"
        "- Length: 300-400 words\n"
        "- Output only the letter body (no date, no addresses \u2014 "
        "those are in the template)"
    )

    user_prompt = (
        f"Write the motivation letter for the position of {job.title} "
        f"at {job.company}."
    )

    return call_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=WRITER_MODEL,
        temperature=0.5,
    )


def generate_cv_dynamic_zones(
    job: JobDescription,
    profile: UserProfile,
    language: str,
) -> CVDynamicZones:
    """Generate dynamic CV content zones tailored to a specific job.

    Produces the structured content that fills the dynamic sections of a
    CV: a two-sentence professional summary, a curated list of relevant
    education subjects, tailored bullet points for each work experience
    entry, and a selection of the most relevant projects. All content is
    generated in the requested *language* and tailored to the job's
    required topics and description.

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
    system_prompt = (
        f"You are an expert CV writer. Generate dynamic CV content in "
        f"{language} tailored to the job below.\n"
        "\n"
        "Instructions:\n"
        "- Write a 3-sentence professional summary that highlights the "
        "candidate's most relevant qualifications for this role.\n"
        "- Select 6-8 relevant subjects from the user's education that "
        "best match the job requirements.\n"
        "- Write 2 bullet points per work experience entry, each tailored "
        "to emphasise duties and achievements that align with this job.\n"
        "- Select the 2 most relevant projects with a one-line description "
        "each.\n"
        "- Output strictly valid JSON matching the provided schema. "
        "No extra text, no markdown fences."
    )

    profile_json = json.dumps(
        profile.model_dump(), indent=2, ensure_ascii=False
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
        model=WRITER_MODEL,
        temperature=0.2,
    )
