"""Generate AI-written content for cover letters and CV dynamic zones.

This module generates the creative text that fills the dynamic sections of job
application documents. It uses the raw-text LLM path for the cover letter body
and the structured-output path for the CV zones that must conform to the
:class:`CVDynamicZones` schema.
"""

import json

from src.llm_client import call_llm, call_llm_parsed, EXTRACTION_MODEL, WRITER_MODEL
from src.models import CVDynamicZones, JobDescription, UserProfile

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

    system_prompt = (
        f"Write a motivation letter in {text_language} for the following position.\n"
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
        "- Length: 230 - 250 words\n"
        "- Output only the letter body (no date, no addresses \u2014 "
        "- Paragraph length: less than 50 words"
        "- Use connectors between sentences so the text is more fluent by reading"
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
    CV: a two-sentence professional summary, one sentence explaining the user's relevant
    bachelor and master degrees subjects

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
    system_prompt = (
        f"You are an expert CV writer. Generate dynamic CV content in "
        f"{text_language} tailored to the job below.\n"
        "\n"
        "Instructions:\n"
        "- Write a 3-sentence professional summary that highlights the "
        "candidate's most relevant qualifications for this role. This text "
        "can NOT have more than 362 characters.\n"
        "- Write one sentence naming user's knowledge through 2-3 bachelor "
        "subjects that are relevant to the job. This sentence can NOT be longer "
        "than 140 characters.\n"
        "- Write one sentence naming user's knowledge through 2-3 master "
        "subjects that are relevant to the job. This sentence can NOT be longer "
        "than 140 characters.\n"
        "RULES:\n"
        "- Be specific and concrete\n"
        "- For professional summary, write the sentences in the first person singular\n"
        "- For bachelor's and master's subjects, write the sentences in a neutral form, not related" 
        "to a specific person, e.g., “Deepened knowledge in CFD” instead of “I deepened my knowledge in CFD.”"

        "- Respond ONLY with valid JSON matching the provided schema."
    )

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
        model=EXTRACTION_MODEL,
        temperature=0.2,
        timeout=180.0,
    )
