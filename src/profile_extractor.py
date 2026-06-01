"""Extract a structured :class:`UserProfile` from background markdown files.

This module provides the first layer of the Bonfire pipeline. It reads
candidate background information from a directory of Markdown files and
uses an LLM to build a structured ``UserProfile`` object, which is then
validated via Pydantic and persisted as JSON.
"""

import json
from pathlib import Path

from src.models import UserProfile
from src.llm_client import call_llm_parsed
from src.config import CONFIG
from src.utils import render_prompt

RELEVANT_FIELDS = [
    "thermal_simulation", "cfd", "experiments", "mechanical_design",
    "turbomachines", "renewable_energy", "fluid_dynamics", "thermodynamics",
    "programming", "machine_learning","agentic workflows"
]


def _read_md_files(md_directory: str) -> dict[str, str]:
    """Read all .md files in *md_directory* and return a mapping of filename -> content.

    Each file's stem (filename without the ``.md`` extension) is used as the
    key in the returned dictionary.

    Args:
        md_directory: Absolute or relative path to the directory containing
            ``.md`` files.

    Returns:
        A dictionary mapping each filename stem to its full text content.

    Raises:
        FileNotFoundError: When the directory contains no ``.md`` files.
    """
    md_dir = Path(md_directory)
    md_paths = sorted(md_dir.glob("*.md"))
    if not md_paths:
        raise FileNotFoundError(f"No .md files found in directory: {md_directory}")

    return {
        path.stem: path.read_text(encoding="utf-8")
        for path in md_paths
    }


def _build_extraction_prompt(md_contents: dict[str, str]) -> str:
    """Build a single user prompt from all markdown file contents.

    Args:
        md_contents: Mapping of filenames to their full Markdown content.

    Returns:
        A single string that concatenates every file under a ``### FILE:``
        header, suitable as the ``user_prompt`` for the LLM extraction call.
    """
    sections = [f"### FILE: {filename}\n{content}" for filename, content in md_contents.items()]

    header = "Below are the candidate's background documents. Extract a complete UserProfile from them.\n\n"
    return header + "\n\n---\n\n".join(sections)


def extract_profile_from_md(md_directory: str, output_json_path: str) -> UserProfile:
    """Extract a UserProfile from all Markdown files in a directory.

    Reads every ``.md`` file in *md_directory*, builds an extraction prompt
    from their contents, calls the LLM with a structured output schema, and
    persists the validated result to the given JSON path.

    Args:
        md_directory: Path to a directory containing ``.md`` files with
            candidate background information.
        output_json_path: Filesystem path where the validated profile will
            be written as pretty-printed JSON.

    Returns:
        The validated :class:`UserProfile` instance.

    Raises:
        FileNotFoundError: If *md_directory* does not exist or contains no
            ``.md`` files (propagated from :func:`_read_md_files`).
        ValidationError: If the LLM output does not conform to the
            :class:`UserProfile` schema (propagated from Pydantic).
    """
    md_contents = _read_md_files(md_directory)
    user_prompt = _build_extraction_prompt(md_contents)

    profile = call_llm_parsed(
        system_prompt=render_prompt(
            "extract_profile",
            relevant_fields=RELEVANT_FIELDS,
        ),
        user_prompt=user_prompt,
        model=CONFIG.models.extraction_model,
        temperature=0.2,
        response_model=UserProfile,
    )

    output_path = Path(output_json_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(profile.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return profile
