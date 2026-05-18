"""Extract job descriptions and evaluate candidate match quality.

This module provides the third step of the Bonfire pipeline. It extracts
structured job descriptions from raw job posting text and evaluates how
well a candidate's profile matches each job, producing a detailed
:class:`JobMatchResult`.

The topic vocabulary in ``VALID_TOPICS`` is duplicated from
``profile_extractor.py`` so that both modules use the same canonical set
of domain tags.
"""

from pydantic import BaseModel

from src.llm_client import call_llm_parsed, EXTRACTION_MODEL
from src.models import JobDescription, JobMatchResult, UserProfile
from src.profile_extractor import RELEVANT_FIELDS
from src.utils import render_prompt

VALID_TOPICS = RELEVANT_FIELDS  

class TopicsResponse(BaseModel):
    """Wrapper for LLM topic extraction output.

    Attributes:
        topics (list[str]): List of topic tags selected from ``VALID_TOPICS``.
    """

    topics: list[str]


def extract_job_topics(raw_text: str) -> list[str]:
    """Extract domain topics from a raw job posting.

    Sends the job text to the LLM and asks it to select relevant topics
    from the predefined ``VALID_TOPICS`` list. The result is filtered to
    guard against LLM hallucination.

    Args:
        raw_text (str): The full, unmodified text of the job posting.

    Returns:
        list[str]: A list of valid topic tags found in the job description.
    """
    system_prompt = render_prompt(
        "extract_job_topics",
        valid_topics=VALID_TOPICS,
    )

    result = call_llm_parsed(
        system_prompt=system_prompt,
        user_prompt=raw_text,
        response_model=TopicsResponse,
        model=EXTRACTION_MODEL,
        temperature=0.1,
    )

    return [t for t in result.topics if t in VALID_TOPICS]


def extract_job_description(raw_text: str) -> JobDescription:
    """Extract a structured job description from raw posting text.

    Sends the job text to the LLM to extract title, company, location,
    and required topics. The original raw text is always preserved on the
    returned model. Required topics are filtered to the valid vocabulary.

    Args:
        raw_text (str): The full, unmodified text of the job posting.

    Returns:
        JobDescription: A validated :class:`JobDescription` with all fields
            populated.
    """
    system_prompt = render_prompt(
        "extract_job_description",
        valid_topics=VALID_TOPICS,
    )

    job = call_llm_parsed(
        system_prompt=system_prompt,
        user_prompt=raw_text,
        response_model=JobDescription,
        model=EXTRACTION_MODEL,
        temperature=0.1,
    )

    job = job.model_copy(update={"raw_text": raw_text})
    job.required_topics = [t for t in job.required_topics if t in VALID_TOPICS]

    return job


def evaluate_job_match(job: JobDescription, profile: UserProfile) -> JobMatchResult:
    """Evaluate how well a candidate's profile matches a job description.

    Sends the job description and candidate profile to the LLM to produce a
    structured match assessment including required qualifications, gaps,
    strengths, and an overall recommendation.

    Args:
        job: The target job description.
        profile: The candidate's full profile.

    Returns:
        A validated :class:`JobMatchResult` instance.
    """
    system_prompt = render_prompt("evaluate_job_match")

    user_prompt = (
        f"JOB: {job.title} at {job.company}\n"
        f"REQUIRED TOPICS: {', '.join(job.required_topics)}\n"
        f"CANDIDATE: {profile.personal_info.name}\n"
        f"PROFILE JSON:\n{profile.model_dump_json(indent=2)}"
    )

    return call_llm_parsed(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_model=JobMatchResult,
        model=EXTRACTION_MODEL,
        temperature=0.2,
    )

