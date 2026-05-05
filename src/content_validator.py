"""Validate AI-generated content against the candidate's real profile.

This module checks generated document text for hallucinations — claims about
the candidate's skills, experience, or qualifications that are NOT supported
by the user profile. It uses :func:`call_llm_parsed` with a
:class:`ValidationFlags` response model to obtain structured validation
results from the LLM.

For the MVP it returns a list of flagged strings.
"""

import json

from pydantic import BaseModel

from src.llm_client import call_llm_parsed, EXTRACTION_MODEL
from src.models import UserProfile


class ValidationFlags(BaseModel):
    """Pydantic response model for structured LLM content-validation output.

    Designed to be used as the ``response_model`` parameter of
    :func:`call_llm_parsed` so that the LLM returns a parseable JSON object
    with a single ``flags`` key.

    Attributes:
        flags: List of hallucinated claim strings found in the text.
            Empty list when no violations are detected.
    """

    flags: list[str]


def validate_content(generated_text: str, profile: UserProfile) -> list[str]:
    """Validate generated text against the candidate's actual profile.

    Sends the generated text and the user profile to an LLM, which flags
    any claims, skills, or experiences in the text that are not supported
    by the profile data. The LLM output is parsed as a
    :class:`ValidationFlags` instance to ensure structured results.

    Args:
        generated_text: The AI-generated document text to validate.
        profile: The candidate's real profile containing verified data.

    Returns:
        A list of flagged claim strings that are not supported by the
        profile. Empty list when no hallucinations are detected.
    """
    system_prompt = (
        "Review the following generated text against the candidate's actual profile.\n"
        "Flag any claims, skills, or experiences mentioned in the text that are NOT "
        "supported by the profile.\n"
        "Output a JSON object with a 'flags' key containing a list of flagged strings.\n"
        "If none, output an empty list."
    )

    user_prompt = (
        f"{generated_text}\n---\n"
        f"{json.dumps(profile.model_dump(), indent=2, ensure_ascii=False)}"
    )

    result = call_llm_parsed(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_model=ValidationFlags,
        model=EXTRACTION_MODEL,
        temperature=0.1,
    )

    return result.flags
